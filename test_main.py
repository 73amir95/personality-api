import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("./test_db.db"):
        try:
            os.remove("./test_db.db")
        except PermissionError:
            print("Could not remove test_db.db - file locked.")


def test_root_redirects_to_login():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 307]


def test_create_user():
    response = client.post(
        "/auth/register-process",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword"
        }
    )
    assert response.status_code in [200, 302]


def test_login_and_cookie_creation():
    response = client.post(
        "/auth/login-process",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=False
    )
    assert "access_token" in response.cookies
    token_value = response.cookies["access_token"].replace('"', '')
    assert token_value.startswith("Bearer")


def test_logout_clears_cookie():
    response = client.get("/auth/logout", follow_redirects=False)
    cookie_header = response.headers.get("set-cookie", "")
    assert 'access_token=""' in cookie_header or 'Max-Age=0' in cookie_header


def test_successful_prediction():
    client.post("/auth/login-process", data={"username": "testuser", "password": "testpassword"})

    prediction_data = {
        "Time_spent_Alone": 5.0,
        "Stage_fear": "No",
        "Social_event_attendance": 2.0,
        "Going_outside": 1.0,
        "Drained_after_socializing": "Yes",
        "Friends_circle_size": 2,
        "Post_frequency": 1.0
    }

    response = client.post("/predict/predict-form", data=prediction_data)
    assert response.status_code == 200
    assert "Result" in response.text