from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities import RoleEnum, Site, User, Client, Trainer

class ISiteRepository(ABC):
    '''Port for site persistence'''

    @abstractmethod
    async def save(self, site: Site) -> Site:
        pass

    @abstractmethod
    async def read_by_id(self, site_id: int) -> Optional[Site]:
        pass

    @abstractmethod
    async def read_all(self) -> List[Site]:
        pass

class IUserRepository(ABC):
    '''Port for user persistence'''

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def read_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def read_by_email(self, email: str) -> Optional[User]:
        pass

    

    @abstractmethod
    async def read_all_by_role(self, role: str):
        pass

    