from fastapi import APIRouter, HTTPException  # Tambahkan APIRouter di sini
from pydantic import BaseModel
from . import db

# Ganti 'app = FastAPI()' dengan baris di bawah ini
router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    company_name: str
    admin_email: str
    password: str

# Ganti '@app.post' menjadi '@router.post'


@router.post("/api/auth/login")
async def login(req: LoginRequest):
    try:
        user_data = db.get_user(req.email)
        if user_data and db.verify_password(req.password, user_data.get("password", "")):
            user_data.pop("password", None)
            return {"status": "success", "user": user_data}
        raise HTTPException(
            status_code=401, detail="Email atau password salah.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ganti '@app.post' menjadi '@router.post'


@router.post("/api/auth/register")
async def register(req: RegisterRequest):
    try:
        db.register_company(req.company_name, req.admin_email, req.password)
        return {"status": "success", "message": "Perusahaan berhasil didaftarkan. Silakan login."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
