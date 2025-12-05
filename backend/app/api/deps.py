"""
認証・権限チェックの依存関係
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Optional
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User, Department

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    現在のユーザーを取得（認証チェック）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報を確認できませんでした",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # sub は文字列として格納されているので、整数に変換
    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise credentials_exception
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは無効です"
        )
    
    return user


async def get_current_user_with_department(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> tuple[User, Department]:
    """
    現在のユーザーと部署を取得
    """
    statement = select(Department).where(Department.id == current_user.department_id)
    department = session.exec(statement).first()
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署が見つかりません"
        )
    return current_user, department


def require_department(*allowed_codes: str):
    """
    部署コードによる権限チェックデコレータ
    使用例: @router.get("/", dependencies=[Depends(require_department("head", "mnet"))])
    """
    async def check_department(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> User:
        statement = select(Department).where(Department.id == current_user.department_id)
        department = session.exec(statement).first()
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部署が見つかりません"
            )
        
        if department.code not in allowed_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"この操作には {', '.join(allowed_codes)} の権限が必要です"
            )
        
        return current_user
    
    return check_department


def require_role(*allowed_roles: str):
    """
    ロールによる権限チェックデコレータ
    
    使用例:
    - @router.get("/", dependencies=[Depends(require_role("admin"))])
    - @router.get("/", dependencies=[Depends(require_role("manager", "head", "admin"))])
    
    ロールの種類:
    - staff: 一般従業員（自分に関係する情報のみ）
    - manager: 部門責任者（自分の部門全体を見られる）
    - head: 本部（全部門を横断して見られる）
    - admin: システム管理者（全機能にアクセス可能）
    """
    async def check_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            role_names = {
                "staff": "スタッフ",
                "manager": "マネージャー",
                "head": "本部",
                "admin": "管理者"
            }
            allowed_names = [role_names.get(r, r) for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"この操作には {', '.join(allowed_names)} の権限が必要です"
            )
        return current_user
    
    return check_role


# よく使う権限チェックのショートカット
def require_admin():
    """管理者のみアクセス可能"""
    return require_role("admin")


def require_manager_or_head():
    """マネージャーまたは本部のみアクセス可能"""
    return require_role("manager", "head", "admin")


def require_head_or_admin():
    """本部または管理者のみアクセス可能"""
    return require_role("head", "admin")

