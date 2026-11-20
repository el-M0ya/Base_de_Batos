"""HTTP schemas for administrator-managed users."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TrainerProfileRequest(BaseModel):
    specialty: str = "GENERAL"


class ClientProfileRequest(BaseModel):
    age: int = Field(ge=14, le=100)
    id_site: int = Field(gt=0)


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: str
    trainer: Optional[TrainerProfileRequest] = None
    client: Optional[ClientProfileRequest] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = Field(default=None, min_length=1)
    password: Optional[str] = Field(default=None, min_length=1)
    role: Optional[str] = None
    active: Optional[bool] = None
    trainer: Optional[TrainerProfileRequest] = None
    client: Optional[ClientProfileRequest] = None


class TrainerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_trainer: int
    specialty: str


class ClientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_client: int
    age: int
    id_site: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_user: int
    name: str
    email: str
    role: str
    active: bool
    created_at: Optional[datetime]
    trainer: Optional[TrainerProfileResponse] = None
    client: Optional[ClientProfileResponse] = None
