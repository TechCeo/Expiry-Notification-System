from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError


@dataclass(frozen=True, slots=True)
class OidcClaims:
    subject: str
    email: str | None
    email_verified: bool
    display_name: str | None
    raw: dict[str, Any]


class SigningKeyProvider(Protocol):
    def get_signing_key_from_jwt(self, token: str): ...


class TokenVerifier:
    def __init__(
        self,
        settings: Settings,
        signing_keys: SigningKeyProvider | None = None,
    ) -> None:
        self.settings = settings
        self.signing_keys = signing_keys or PyJWKClient(
            settings.oidc_jwks_url,
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=settings.oidc_jwks_cache_seconds,
        )

    def verify(self, token: str) -> OidcClaims:
        try:
            signing_key = self.signing_keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self._algorithms,
                audience=self.settings.oidc_audience,
                issuer=self.settings.oidc_issuer_url,
                options={"require": ["exp", "sub"]},
            )
        except (PyJWTError, ValueError, OSError) as error:
            raise AuthenticationError("The access token is invalid or expired.") from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("The access token has no valid subject.")
        email = claims.get("email")
        email_verified = claims.get("email_verified") is True
        name = claims.get("name") or claims.get("preferred_username")
        return OidcClaims(
            subject=subject,
            email=email if isinstance(email, str) else None,
            email_verified=email_verified,
            display_name=name if isinstance(name, str) else None,
            raw=claims,
        )

    @property
    def _algorithms(self) -> list[str]:
        algorithms = [value.strip() for value in self.settings.oidc_algorithms.split(",")]
        allowed = [value for value in algorithms if value]
        if not allowed or any(value.startswith("HS") or value == "none" for value in allowed):
            raise AuthenticationError("The API has no safe asymmetric JWT algorithm configured.")
        return allowed


@lru_cache
def get_token_verifier() -> TokenVerifier:
    return TokenVerifier(get_settings())
