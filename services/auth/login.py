from sqlmodel import Session

from app.crud import getUserByUsername
from app.crud import verifyPassword

# 验证用户
def authenticateUser(db: Session, username: str, password: str):
    user = getUserByUsername(db, username)
    if not user:
        return False
    
    if not verifyPassword(password, user.hashedPassword):
        return False
    return user