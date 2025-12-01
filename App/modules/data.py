from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AnalysisBase(BaseModel):
    original_text: str
    analysis_results: Dict[str, Any]

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisResponse(AnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisHistoryResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int

class OAuth2PasswordRequestForm:
    def __init__(
        self,
        username: str,
        password: str,
        scope: str = "",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret