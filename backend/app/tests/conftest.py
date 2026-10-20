import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.core.permissions import UserRole
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User

# Use an isolated in-memory or test SQLite database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_gbmarket.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db):
    user = db.query(User).filter(User.email == "admin.test@gbmarket.pk").first()
    if not user:
        user = User(
            email="admin.test@gbmarket.pk",
            phone="03401111111",
            full_name="Test Admin",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture
def customer_user(db):
    user = db.query(User).filter(User.email == "customer.test@gbmarket.pk").first()
    if not user:
        user = User(
            email="customer.test@gbmarket.pk",
            phone="03402222222",
            full_name="Test Customer",
            hashed_password=hash_password("CustomerPass123!"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    return create_access_token(subject=admin_user.id, role=admin_user.role)

@pytest.fixture
def customer_token(customer_user):
    return create_access_token(subject=customer_user.id, role=customer_user.role)
