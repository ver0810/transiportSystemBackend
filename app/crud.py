from jose import jwt
from fastapi import HTTPException
from sqlmodel import Session, select
from datetime import timedelta, datetime
from passlib.context import CryptContext

from app.models import User
from app.schemas import RegisterUser

# JWT 配置
SECRET_KEY = "your-secret-key"  # 替换为一个安全的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 哈希密码
def getHashedPassword(password: str):
    return pwd_context.hash(password)


# 验证函数
def verifyPassword(plainPassword: str, hashedPassword: str):
    return pwd_context.verify(plainPassword, hashedPassword)


# 创建JWT
def createAccessToken(data: dict, expiresDelta: timedelta):
    toEncode = data.copy()
    expires = datetime.now() + expiresDelta
    toEncode.update({"exp": expires})
    encodeJwt = jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)
    return encodeJwt


# 用户名查找
def getUserByUsername(db: Session, username: str):
    statement = select(User).where(User.username == username)
    dbUser = db.exec(statement).first()
    return dbUser

# 创建用户
def createUser(db: Session, user: RegisterUser):
    # 检查用户是否存在
    if getUserByUsername(db, user.username):
        raise HTTPException(status_code=400, detail="User has registered")
    dbUser = User(**user.model_dump())
    dbUser.hashedPassword = getHashedPassword(user.password)
    db.add(dbUser)
    db.commit()
    db.refresh(dbUser)
    return dbUser

# 更新用户名
def updateUsername(db: Session, current_username: str, new_username: str):
    # 检查新用户名是否已存在
    if getUserByUsername(db, new_username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 获取当前用户
    user = getUserByUsername(db, current_username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新用户名
    user.username = new_username
    db.commit()
    db.refresh(user)
    return user

# 更新用户密码
def updatePassword(db: Session, username: str, current_password: str, new_password: str):
    # 获取用户
    user = getUserByUsername(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 验证当前密码
    if not verifyPassword(current_password, user.hashedPassword):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # 更新密码
    user.hashedPassword = getHashedPassword(new_password)
    db.commit()
    db.refresh(user)
    return user
