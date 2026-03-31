from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user
from src.models.user import UserCreate, UserLogin, TokenResponse
from src.services import auth_service, db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: UserCreate):
    existing = await db.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = auth_service.hash_password(body.password)
    user = await db.create_user(body.email, hashed)
    token = auth_service.create_access_token(str(user["id"]))

    return TokenResponse(access_token=token, user_id=str(user["id"]), email=user["email"])


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = await db.get_user_by_email(body.email)
    if not user or not auth_service.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth_service.create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user_id=str(user["id"]), email=user["email"])


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user_id": str(current_user["id"]), "email": current_user["email"]}
