from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """从请求头 Authorization: Bearer <token> 中解析当前用户"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或缺少 Token")

    token = auth_header.removeprefix("Bearer ").strip()
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
