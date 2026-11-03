from collections.abc import Generator
from typing import Any

import psycopg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from src.core.config import settings
from src.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db_cursor() -> Generator[psycopg.Cursor, None, None]:
    with psycopg.connect(settings.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            yield cur
        conn.commit()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    company_id = payload.get("company_id")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id or not company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user_id,
        "company_id": str(company_id),
        "email": email,
        "role": role,
    }


def get_client_ip(request: Request) -> str:
    # Read from trusted proxy header or client host
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"
