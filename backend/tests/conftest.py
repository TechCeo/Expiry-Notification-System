from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.authentication import get_current_user
from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.main import app

test_engine = create_engine(get_settings().database_url, pool_pre_ping=True)


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    outer_transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture
def authenticated_user(database_session: Session) -> User:
    user = User(
        oidc_subject="integration-owner-subject",
        email="owner@example.com",
        email_verified=True,
        display_name="Integration Owner",
    )
    database_session.add(user)
    database_session.flush()
    database_session.commit()
    return user


@pytest.fixture
def client(
    database_session: Session, authenticated_user: User
) -> Generator[TestClient, None, None]:
    def override_database() -> Generator[Session, None, None]:
        try:
            yield database_session
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_current_user] = lambda: authenticated_user
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
