from getpass import GetPassWarning
from uuid import uuid4
import warnings

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import create_admin as command
from app.auth.service import password_hasher
from app.models import User

PASSWORD = "admin test passphrase"


def mock_passwords(monkeypatch, first=PASSWORD, second=PASSWORD):
    answers = iter([first, second])
    monkeypatch.setattr(command, "getpass", lambda prompt: next(answers))


@pytest.mark.integration
def test_command_creates_admin_that_can_login(registration, monkeypatch, capsys):
    client, connection = registration
    email = f"Admin.{uuid4().hex}@example.com"
    mock_passwords(monkeypatch)
    monkeypatch.setattr(command, "get_engine", lambda: connection)
    monkeypatch.setattr(command, "Session", lambda bind: Session(bind, join_transaction_mode="create_savepoint"))
    monkeypatch.setenv("JWT_SECRET", "test-only-admin-secret-with-at-least-32-characters")

    assert command.main(["--email", f" {email.upper()} ", "--name", " Admin User "]) == 0
    output = capsys.readouterr()
    assert "Created admin with ID" in output.out
    assert PASSWORD not in output.out + output.err
    user = connection.execute(select(User.__table__).where(User.email == email.lower())).one()
    assert user.role == "admin"
    assert user.name == "Admin User"
    assert user.default_address is None
    assert password_hasher.verify(PASSWORD, user.password_hash)
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200
    profile = client.get("/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert profile.json()["role"] == "admin"


@pytest.mark.integration
@pytest.mark.parametrize("role", ["customer", "staff", "admin"])
def test_duplicate_command_does_not_modify_existing_user(registration, monkeypatch, capsys, role):
    _, connection = registration
    email = f"existing-{uuid4().hex}@example.com"
    original_hash = password_hasher.hash("original password")
    user_id = connection.scalar(User.__table__.insert().values(
        email=email, name="Original", role=role, password_hash=original_hash,
    ).returning(User.id))
    monkeypatch.setattr(command, "get_engine", lambda: connection)
    monkeypatch.setattr(command, "Session", lambda bind: Session(bind, join_transaction_mode="create_savepoint"))
    mock_passwords(monkeypatch)

    assert command.main(["--email", email.upper(), "--name", "Replacement"]) == 1
    assert "Existing account was not changed" in capsys.readouterr().err
    saved = connection.execute(select(User.__table__).where(User.id == user_id)).one()
    assert (saved.name, saved.role, saved.password_hash) == ("Original", role, original_hash)


@pytest.mark.parametrize("email,name,password,confirmation", [
    ("admin@example.com", "Admin", PASSWORD, "different password"),
    ("bad-email", "Admin", PASSWORD, PASSWORD),
    ("admin@example.com", "   ", PASSWORD, PASSWORD),
    ("admin@example.com", "Admin", "tiny", "tiny"),
])
def test_invalid_input_never_opens_database(monkeypatch, capsys, email, name, password, confirmation):
    mock_passwords(monkeypatch, password, confirmation)
    monkeypatch.setattr(command, "get_engine", lambda: pytest.fail("Database should not be opened"))
    assert command.main(["--email", email, "--name", name]) == 1
    output = capsys.readouterr()
    assert "Created admin" not in output.out
    assert password not in output.out + output.err


def test_no_hidden_input_cancels_command(monkeypatch, capsys):
    # Simulate a terminal that cannot hide password input, such as an IDE Debug
    # Console, a CI job without an interactive terminal, or redirected input.
    # The command should cancel instead of falling back to visible input,
    # without accessing the database.
    def unavailable(prompt):
        warnings.warn("Cannot hide input", GetPassWarning)

    monkeypatch.setattr(command, "getpass", unavailable)
    monkeypatch.setattr(command, "get_engine", lambda: pytest.fail("Database should not be opened"))
    assert command.main(["--email", "admin@example.com", "--name", "Admin"]) == 1
    assert "hidden password input" in capsys.readouterr().err
