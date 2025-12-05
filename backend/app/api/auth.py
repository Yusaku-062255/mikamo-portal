from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
from app.core.database import get_session
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User, Department
from app.models.business_unit import BusinessUnit
from app.api.deps import get_current_user
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    department_id: int


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    department_id: int
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    business_unit_id: Optional[int] = None
    business_unit_name: Optional[str] = None
    tenant_id: Optional[int] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """ユーザー登録"""
    # 既存ユーザーをチェック
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    # ユーザー作成
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department_id=user_data.department_id
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """ログイン"""
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは無効です"
        )
    
    # 部署情報を取得
    statement = select(Department).where(Department.id == user.department_id)
    department = session.exec(statement).first()
    department_code = department.code if department else ""
    
    # JWTトークンに user_id, role, department_code を含める
    # sub は JWT仕様で文字列である必要がある
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "department_code": department_code
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """現在のユーザー情報を取得（部門情報を含む）"""
    # 部門情報を取得
    statement = select(Department).where(Department.id == current_user.department_id)
    department = session.exec(statement).first()

    # 事業部門情報を取得
    business_unit = None
    if current_user.business_unit_id:
        business_unit = session.get(BusinessUnit, current_user.business_unit_id)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        department_id=current_user.department_id,
        department_name=department.name if department else None,
        department_code=department.code if department else None,
        business_unit_id=current_user.business_unit_id,
        business_unit_name=business_unit.name if business_unit else None,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
        is_active=current_user.is_active
    )

