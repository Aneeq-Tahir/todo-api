from fastapi.testclient import TestClient
from src.database import get_db, Users, SQLModel
from sqlmodel import create_engine, Session, select
from src.auth import generate_access_token
from src.settings import TEST_DATABASE_URL
from src.main import app
import pytest

conn_str = str(TEST_DATABASE_URL)
engine = create_engine(conn_str)


def override_get_db():
    db = Session(bind=engine)
    return db


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def get_user_token():
    SQLModel.metadata.create_all(bind=engine)
    with override_get_db() as db:
        existing_user = db.exec(
            select(Users).where(Users.email == "testuser@example.com")
        ).first()

        # Check if user already exists in the database
        if existing_user:
            # If user already exists, create token
            access_token = generate_access_token(
                email=existing_user.email,
                user_id=existing_user.id,
            )

            yield access_token
            db.delete(existing_user)
            db.commit()
        else:
            # Else if user doesn't exist, create a new user
            new_user = Users(email="testuser@example.com", hashed_password="hellotest")
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            access_token = generate_access_token(
                email=new_user.email,
                user_id=new_user.id,
            )

            yield access_token
            db.delete(new_user)
            db.commit()


def test_create_todo(client: TestClient, get_user_token):
    token = get_user_token
    todo_data = {"description": "Test Todo", "completed": False}
    response = client.post(
        "/api/todo", json=todo_data, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Todo added successfully"}


def test_get_user_todos(client: TestClient, get_user_token):
    token = get_user_token
    response = client.get("/api/todo", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "todos" in response.json()


def test_update_todo(client: TestClient, get_user_token):
    token = get_user_token
    response = client.get("/api/todo", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    todos = response.json().get("todos")

    todo_id: int = todos[0].get("id")

    updated_todo_data = {"description": "Updated Todo Description", "completed": True}
    response = client.put(
        f"/api/todo/{todo_id}",
        json=updated_todo_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Todo updated successfully"}


def test_delete_todo(client: TestClient, get_user_token):
    token = get_user_token
    response = client.get("/api/todo", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    todos = response.json().get("todos")

    todo_id: int = todos[0].get("id")

    response = client.delete(
        f"/api/todo/{todo_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Todo deleted successfully"}
