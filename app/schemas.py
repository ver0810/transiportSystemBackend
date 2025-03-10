from pydantic import BaseModel
from sqlalchemy import JSON


class UserBase(BaseModel):
    username: str

# 注册请求模型
class RegisterUser(BaseModel):
    username: str
    password: str


# 登录请求模型
class LoginUser(BaseModel):
    username: str
    password: str


# 数据库存储用户模型
class UserInDB(UserBase):
    hashedPassword: str


# 数据库存储路网信息模型
class RoadNetworkRequest(BaseModel):
    geom: str  # WKT 格式

# 定义请求体模型
class UsernameUpdateRequest(BaseModel):
    current_username: str
    new_username: str

# 定义请求体模型
class PasswordUpdateRequest(BaseModel):
    username: str
    current_password: str
    new_password: str