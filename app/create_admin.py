"""Create an admin from a trusted local terminal, never through public signup."""
import argparse
from getpass import GetPassWarning, getpass
import sys
import warnings

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest
from app.auth.service import EmailAlreadyRegistered, password_hasher
from app.db import get_engine
from app.models import User


def create_admin(session: Session, data: RegisterRequest) -> int:
    user = User(
        email=str(data.email), name=data.name, role="admin",
        password_hash=password_hasher.hash(data.password.get_secret_value()),
    )
    session.add(user)
    try:
        session.flush()
        user_id = user.id
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "uq_users_email":
            raise EmailAlreadyRegistered from error
        raise
    return user_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a local admin account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    try:
        # Refuse getpass's fallback to visible input if no secure terminal exists.
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            password = getpass("Password: ")
            confirmation = getpass("Confirm password: ")
        if password != confirmation:
            print("Passwords do not match. No account created.", file=sys.stderr)
            return 1
        data = RegisterRequest(email=args.email, name=args.name, password=password)
        with Session(get_engine()) as session:
            user_id = create_admin(session, data)
    except ValidationError as error:
        # Do not print input values from validation errors (including passwords).
        for item in error.errors(include_input=False, include_context=False):
            print(f"{'.'.join(map(str, item['loc']))}: {item['msg']}", file=sys.stderr)
        return 1
    except EmailAlreadyRegistered:
        print("Email already exists. Existing account was not changed.", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Database operation failed. Check PostgreSQL and migrations.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt, GetPassWarning):
        print("Cancelled: a terminal with hidden password input is required.", file=sys.stderr)
        return 1
    print(f"Created admin with ID {user_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
