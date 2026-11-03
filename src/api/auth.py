from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from src.api.deps import get_client_ip, get_current_user, get_db_cursor
from src.core.rate_limit import AuthThrottle, ThrottleResult
from src.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
auth_throttle = AuthThrottle(ip_limit=30, failure_limit=5, cooldown_seconds=60)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    company_id: str
    company_name: str


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, response: Response, cur=Depends(get_db_cursor)):
    client_ip = get_client_ip(request)
    email_clean = req.email.strip().lower()

    # Query user & company
    cur.execute("""
        SELECT u.id, u.company_id, u.email, u.password_hash, u.full_name, u.role, u.is_active, c.name
        FROM users u
        JOIN companies c ON u.company_id = c.id
        WHERE u.email = %s;
    """, (email_clean,))
    user_row = cur.fetchone()

    is_valid = False
    if user_row:
        stored_hash = user_row[3]
        is_active = user_row[6]
        if is_active and verify_password(req.password, stored_hash):
            is_valid = True

    # Record attempt in rate limiter
    throttle_res = auth_throttle.record_attempt(ip=client_ip, email=email_clean, success=is_valid)

    if throttle_res.status == ThrottleResult.IP_LIMITED:
        response.headers["Retry-After"] = str(throttle_res.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Terlalu banyak permintaan dari IP ini. Coba lagi dalam {throttle_res.retry_after_seconds} detik.",
        )

    if throttle_res.status == ThrottleResult.ACCOUNT_COOLDOWN:
        response.headers["Retry-After"] = str(throttle_res.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Akun terkunci sementara karena 5 kali percobaan gagal. Coba lagi dalam {throttle_res.retry_after_seconds} detik.",
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    u_id, c_id, u_email, _, u_name, u_role, _, c_name = user_row

    token_payload = {
        "sub": str(u_id),
        "company_id": str(c_id),
        "email": u_email,
        "role": u_role,
    }
    token = create_access_token(token_payload)

    return LoginResponse(
        access_token=token,
        user_id=str(u_id),
        email=u_email,
        full_name=u_name,
        role=u_role,
        company_id=str(c_id),
        company_name=c_name,
    )


@router.get("/me")
def get_me(user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    cur.execute("""
        SELECT u.id, u.company_id, u.email, u.full_name, u.role, c.name, c.npwp
        FROM users u
        JOIN companies c ON u.company_id = c.id
        WHERE u.id = %s;
    """, (int(user["id"]),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

    return {
        "id": str(row[0]),
        "company_id": str(row[1]),
        "email": row[2],
        "full_name": row[3],
        "role": row[4],
        "company_name": row[5],
        "company_npwp": row[6],
    }
