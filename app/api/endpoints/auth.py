from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead
from app.schemas.user import UserCreate as UserCreateSchema
from app.services.auth import authenticate_user, create_user, create_access_token, get_current_user_dependency

router = APIRouter(prefix="/auth", tags=["auth"])

from sqlalchemy.exc import IntegrityError

@router.post("/register", response_model=UserRead)
async def register_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await create_user(session, user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user_dependency)
):
    return current_user
