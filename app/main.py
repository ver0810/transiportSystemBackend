from sqlmodel import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status

from app.crud import createUser
from app.database import getSession
from app.schemas import LoginUser, RegisterUser
from services.auth.login import authenticateUser
from app.crud import ACCESS_TOKEN_EXPIRE_MINUTES, createAccessToken

app = FastAPI()

# CORS
origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
@app.post("/user/register")
def createNewUser(user: RegisterUser, db: Session = Depends(getSession)):
    createUser(db, user)
    return {"message": "User registered successfully"}


# 登录路由
@app.post("/user/login")
def login(loginUser: LoginUser, db: Session = Depends(getSession)):
    user = authenticateUser(db, loginUser.username, loginUser.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    accessTokenExpires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    accessToken = createAccessToken(
        data={"sub": user.username}, expiresDelta=accessTokenExpires
    )
    return accessToken