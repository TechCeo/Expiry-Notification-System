from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import TokenVerifier, get_token_verifier
from app.db.models import User
from app.db.session import get_db
from app.repositories.identity import IdentityRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    database: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("A Bearer access token is required.")

    claims = verifier.verify(credentials.credentials)
    repository = IdentityRepository(database)
    user = repository.get_user_by_subject(claims.subject)
    if user is None:
        user = User(
            oidc_subject=claims.subject,
            email=claims.email if claims.email_verified else None,
            email_verified=claims.email_verified,
            display_name=claims.display_name,
        )
        try:
            user = repository.add(user)
        except IntegrityError:
            database.rollback()
            user = repository.get_user_by_subject(claims.subject)
            if user is None:
                raise AuthenticationError(
                    "The identity provider profile conflicts with an existing user."
                )
    else:
        if claims.email is not None and claims.email_verified:
            user.email = claims.email
            user.email_verified = True
        elif claims.email is not None:
            user.email = None
            user.email_verified = False
        if claims.display_name is not None:
            user.display_name = claims.display_name
        try:
            repository.flush(user)
        except IntegrityError as error:
            database.rollback()
            raise AuthenticationError(
                "The identity provider profile conflicts with an existing user."
            ) from error

    if not user.is_active:
        raise PermissionDeniedError("This user account is inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
