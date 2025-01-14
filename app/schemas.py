from pydantic import BaseModel, EmailStr


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

