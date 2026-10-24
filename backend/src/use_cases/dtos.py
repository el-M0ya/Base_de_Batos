from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from src.domain.entities import RoleEnum, TrainerSpecialtyEnum

#  -- DTOs for Site --

class SiteInputDTO(BaseModel):
    ''' Generic DTO to create a new Site in the system'''
    name: str = Field(..., min_length=3, max_length=100, description="Name of the Site")
    address: str = Field(..., min_length=5, description="Site's address")


class SiteOutputDTO(BaseModel):
    ''' Data returned by the app'''
    id: int
    name: str
    address: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

#  -- DTOs for User and Roles --

class UserInputDTO(BaseModel):
    '''Generic DTO to register any user'''
    name: str = Field(..., min_length=3, max_length=60)
    email: EmailStr
    password: str = Field(..., min_length=6, description="Plain password before hashing")
    role: RoleEnum

    ''' Client Fields'''
    site_id: Optional[int] = Field(default=None, description="Required if user is Client")
    age: Optional[int] = Field(default=18, description="Required if user is Client")

    '''Trainer Fields'''
    specialty: Optional[TrainerSpecialtyEnum]

class UserOutputDTO(BaseModel):
    '''Safe answer DTO (Doesnt expose hashed password)'''
    id: int 
    name: str
    email: str
    role: RoleEnum
    created_at: Optional[datetime] = None

    '''extended attributes'''
    specialty: Optional[TrainerSpecialtyEnum] = None
    site_id: Optional[int] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True

#  -- Login & Auth DTOs -- 
class LoginInputDTO(BaseModel):
    """Login credentials""" 
    email: EmailStr 
    password: str 

class TokenOutputDTO(BaseModel):
    """JWT token answer after a successful """     
    access_token: str 
    token_type: str = "bearer"
