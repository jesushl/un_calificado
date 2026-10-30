from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import UserRole, UserStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    role: UserRole = UserRole.CLIENTE
    privacy_consent_version: str = Field(min_length=1, max_length=80)
    adult_declaration: bool

    @model_validator(mode="after")
    def validate_public_role(self):
        if self.role == UserRole.ADMINISTRADOR:
            raise ValueError("El rol administrador se aprovisiona internamente")
        if not self.adult_declaration:
            raise ValueError("Se requiere declarar mayoría de edad")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    status: UserStatus
    privacy_consent_version: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse
