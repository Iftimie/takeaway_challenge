from datetime import datetime, timedelta, timezone

import jwt

from app.config import AuthSettings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    settings = AuthSettings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=ALGORITHM,
    )


def decode_user_id(token: str) -> int:
    claims = jwt.decode(
        token,
        AuthSettings().jwt_secret.get_secret_value(),
        algorithms=[ALGORITHM],
        options={"require": ["sub", "iat", "exp"]},
    )
    subject = claims["sub"]
    # Match PostgreSQL's positive INTEGER IDs; reject malformed/oversized IDs
    # before issuing a database query.
    if (
        not isinstance(subject, str)
        or not subject.isascii()
        or not subject.isdecimal()
        or len(subject) > 10
        or not 1 <= int(subject) <= 2147483647
    ):
        raise jwt.InvalidTokenError("Invalid subject")
    return int(subject)
