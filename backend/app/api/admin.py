"""
管理者用API（ユーザー管理）

admin ロールのみアクセス可能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.core.database import get_session
from app.core.security import get_password_hash
from app.models.user import User, Department
from app.api.deps import get_current_user, require_admin

router = APIRouter()


# リクエスト/レスポンスモデル
class UserCreateRequest(BaseModel):
    """新規ユーザー作成リクエスト"""
    email: EmailStr
    password: str  # 初期パスワード
    full_name: str
    department_id: int
    role: str  # "staff", "manager", "head", "admin"


class UserUpdateRequest(BaseModel):
    """ユーザー更新リクエスト"""
    full_name: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: int
    email: str
    full_name: str
    department_id: int
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class DepartmentResponse(BaseModel):
    """部門情報レスポンス"""
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    department_id: Optional[int] = Query(None, description="部門IDで絞り込み"),
    role: Optional[str] = Query(None, description="ロールで絞り込み"),
    is_active: Optional[bool] = Query(None, description="有効/無効で絞り込み"),
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    ユーザー一覧を取得（管理者のみ）
    
    絞り込み条件:
    - department_id: 部門ID
    - role: ロール（staff, manager, head, admin）
    - is_active: 有効/無効
    """
    statement = select(User)
    
    # 絞り込み条件を追加
    if department_id is not None:
        statement = statement.where(User.department_id == department_id)
    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    
    users = session.exec(statement).all()
    
    # 部門情報を取得してレスポンスに含める
    result = []
    for user in users:
        department = session.get(Department, user.department_id)
        result.append(UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            department_id=user.department_id,
            department_name=department.name if department else None,
            department_code=department.code if department else None,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else ""
        ))
    
    return result


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    部門一覧を取得（管理者のみ）
    """
    statement = select(Department)
    departments = session.exec(statement).all()
    return departments


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    新規ユーザーを作成（管理者のみ）
    
    初期パスワードは別途安全な方法で共有してください。
    """
    # ロールのバリデーション
    allowed_roles = ["staff", "manager", "head", "admin"]
    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ロールは {', '.join(allowed_roles)} のいずれかを指定してください"
        )
    
    # 既存ユーザーをチェック
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    # 部門の存在確認
    department = session.get(Department, user_data.department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された部門が見つかりません"
        )
    
    # パスワードをハッシュ化
    hashed_password = get_password_hash(user_data.password)
    
    # ユーザーを作成
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department_id=user_data.department_id,
        role=user_data.role,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 部門情報を取得
    department = session.get(Department, user.department_id)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        department_name=department.name if department else None,
        department_code=department.code if department else None,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    ユーザー情報を更新（管理者のみ）
    
    更新可能な項目:
    - full_name: 氏名
    - department_id: 部門ID
    - role: ロール
    - is_active: 有効/無効フラグ
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # 更新可能な項目を更新
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.department_id is not None:
        # 部門の存在確認
        department = session.get(Department, user_data.department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された部門が見つかりません"
            )
        user.department_id = user_data.department_id
    if user_data.role is not None:
        # ロールのバリデーション
        allowed_roles = ["staff", "manager", "head", "admin"]
        if user_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ロールは {', '.join(allowed_roles)} のいずれかを指定してください"
            )
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 部門情報を取得
    department = session.get(Department, user.department_id)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        department_name=department.name if department else None,
        department_code=department.code if department else None,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    ユーザー情報を取得（管理者のみ）
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # 部門情報を取得
    department = session.get(Department, user.department_id)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        department_name=department.name if department else None,
        department_code=department.code if department else None,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )

