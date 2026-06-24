from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.authentication import get_current_user
from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import OidcClaims, TokenVerifier, get_token_verifier
from app.db.models import User
from app.db.session import get_db
from app.main import app

API = "/api/v1"


def add_user(
    database_session: Session, *, subject: str, email: str, name: str
) -> User:
    user = User(
        oidc_subject=subject,
        email=email,
        email_verified=True,
        display_name=name,
    )
    database_session.add(user)
    database_session.flush()
    database_session.commit()
    return user


def test_inventory_routes_require_bearer_authentication() -> None:
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.get(f"{API}/organizations")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


class StubTokenVerifier:
    def verify(self, token: str) -> OidcClaims:
        assert token == "provision-user"
        return OidcClaims(
            subject="provisioned-subject",
            email="provisioned@example.com",
            email_verified=True,
            display_name="Provisioned User",
            raw={"sub": "provisioned-subject"},
        )


def test_first_valid_token_provisions_user_without_storing_passwords(
    database_session: Session,
) -> None:
    def override_database():
        try:
            yield database_session
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_token_verifier] = lambda: StubTokenVerifier()
    try:
        with TestClient(app) as provisioning_client:
            response = provisioning_client.get(
                f"{API}/me", headers={"Authorization": "Bearer provision-user"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert response.json()["email"] == "provisioned@example.com"
    assert response.json()["email_verified"] is True
    assert response.json()["memberships"] == []
    provisioned = database_session.query(User).filter_by(
        oidc_subject="provisioned-subject"
    ).one()
    assert provisioned.display_name == "Provisioned User"


def test_roles_tenant_scope_memberships_and_audit(
    client: TestClient,
    database_session: Session,
    authenticated_user: User,
) -> None:
    organization = client.post(
        f"{API}/organizations",
        json={"name": "Secured Organization", "slug": "secured-organization"},
    ).json()
    second_organization = client.post(
        f"{API}/organizations",
        json={"name": "Owner Only", "slug": "owner-only"},
    ).json()
    viewer = add_user(
        database_session,
        subject="viewer-subject",
        email="viewer@example.com",
        name="Inventory Viewer",
    )

    membership_response = client.post(
        f"{API}/organizations/{organization['id']}/memberships",
        json={"user_email": viewer.email, "role": "viewer"},
    )
    assert membership_response.status_code == 201, membership_response.text
    membership = membership_response.json()

    app.dependency_overrides[get_current_user] = lambda: viewer
    scoped = client.get(f"{API}/organizations")
    assert scoped.status_code == 200
    assert scoped.json()["total"] == 1
    assert scoped.json()["items"][0]["id"] == organization["id"]
    assert second_organization["id"] not in {
        item["id"] for item in scoped.json()["items"]
    }

    forbidden_product = client.post(
        f"{API}/products",
        json={
            "organization_id": organization["id"],
            "sku": "VIEWER-CANNOT-WRITE",
            "name": "Forbidden Product",
        },
    )
    assert forbidden_product.status_code == 403
    assert client.get(
        f"{API}/organizations/{organization['id']}/memberships"
    ).status_code == 403
    assert client.get(
        f"{API}/organizations/{second_organization['id']}"
    ).status_code == 403

    app.dependency_overrides[get_current_user] = lambda: authenticated_user
    promoted = client.patch(
        f"{API}/organizations/{organization['id']}/memberships/{membership['id']}",
        json={"role": "inventory_manager"},
    )
    assert promoted.status_code == 200

    app.dependency_overrides[get_current_user] = lambda: viewer
    product = client.post(
        f"{API}/products",
        json={
            "organization_id": organization["id"],
            "sku": "MANAGER-CAN-WRITE",
            "name": "Authorized Product",
        },
    )
    assert product.status_code == 201, product.text
    assert client.patch(
        f"{API}/organizations/{organization['id']}", json={"name": "Forbidden"}
    ).status_code == 403

    app.dependency_overrides[get_current_user] = lambda: authenticated_user
    audit = client.get(f"{API}/organizations/{organization['id']}/audit-events")
    assert audit.status_code == 200
    actions = {event["action"] for event in audit.json()["items"]}
    assert {
        "organization.created",
        "membership.created",
        "membership.updated",
        "product.created",
    }.issubset(actions)

    owner_membership = next(
        value
        for value in client.get(
            f"{API}/organizations/{organization['id']}/memberships"
        ).json()
        if value["user_id"] == str(authenticated_user.id)
    )
    last_owner = client.delete(
        f"{API}/organizations/{organization['id']}/memberships/{owner_membership['id']}"
    )
    assert last_owner.status_code == 422
    assert "at least one owner" in last_owner.json()["detail"]


class StaticSigningKey:
    def __init__(self, key) -> None:
        self.key = key


class StaticKeyProvider:
    def __init__(self, public_key) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> StaticSigningKey:
        assert token
        return StaticSigningKey(self.public_key)


def test_oidc_token_verifier_checks_signature_issuer_audience_and_expiry() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings = Settings(
        oidc_issuer_url="https://issuer.example.com/",
        oidc_audience="expiry-api-test",
        oidc_jwks_url="https://issuer.example.com/jwks.json",
    )
    verifier = TokenVerifier(settings, StaticKeyProvider(private_key.public_key()))
    now = datetime.now(UTC)
    claims = {
        "sub": "oidc-user-123",
        "email": "oidc@example.com",
        "email_verified": True,
        "name": "OIDC User",
        "iss": settings.oidc_issuer_url,
        "aud": settings.oidc_audience,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")

    verified = verifier.verify(token)
    assert verified.subject == "oidc-user-123"
    assert verified.email == "oidc@example.com"
    assert verified.email_verified is True

    wrong_audience = jwt.encode(
        {**claims, "aud": "another-api"}, private_key, algorithm="RS256"
    )
    with pytest.raises(AuthenticationError):
        verifier.verify(wrong_audience)

    wrong_issuer = jwt.encode(
        {**claims, "iss": "https://wrong-issuer.example.com/"},
        private_key,
        algorithm="RS256",
    )
    with pytest.raises(AuthenticationError):
        verifier.verify(wrong_issuer)

    expired = jwt.encode(
        {**claims, "exp": now - timedelta(seconds=1)},
        private_key,
        algorithm="RS256",
    )
    with pytest.raises(AuthenticationError):
        verifier.verify(expired)
