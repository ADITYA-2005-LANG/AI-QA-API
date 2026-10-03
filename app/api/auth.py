from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import create_access_token, verify_password
from app.services.database import (
    get_db_connection,
    release_db_connection
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password_hash, role FROM users WHERE username = %s",
            (request.username,)
        )

        user = cursor.fetchone()
        cursor.close()

    finally:
        release_db_connection(conn)

    if user is None or not verify_password(request.password, user[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = create_access_token(user[0], user[2])

    return {
        "access_token": token,
        "token_type": "bearer"
    }
