from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from App.modules.database import get_db
from App.modules.auth import get_current_user
from App.modules.models import User
from App.modules.logger import get_logger
from typing import Optional

logger = get_logger("dependencies")

async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получает текущего пользователя (опционально)"""
    try:
        # Пытаемся получить токен из cookie (для веб-интерфейса)
        token = request.cookies.get("access_token")
        if not token:
            # Если нет в cookie, пробуем из заголовка Authorization
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.replace("Bearer ", "")
        
        if not token:
            return None
        
        user = await get_current_user(token, db)
        return user
    except Exception as e:
        logger.debug(f"Failed to get user from token: {str(e)}")
        return None

async def get_current_user_required(
    current_user: User = Depends(get_current_user_optional)
) -> User:
    """Требует аутентифицированного пользователя"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user