from typing import Callable, cast 
from src.domain.entities import User, Client, Trainer, RoleEnum, TrainerSpecialtyEnum 
from src.domain.exceptions import ExistingEmailException, InvalidEmailException, InvalidUserAge, PersistenceException 
from src.use_cases.dtos import UserInputDTO, UserOutputDTO 
from src.use_cases.ports.repositories import IUserRepository, ISiteRepository

class UserManagementUseCase:
    def __init__(self, user_repo: IUserRepository, site_repo: ISiteRepository, password_hasher: Callable[[str], str]):
        self.user_repo = user_repo
        self.site_repo = site_repo
        self.password_hasher = password_hasher

    async def register_user(self, dto: UserInputDTO) -> UserOutputDTO:
        
        #Validate existing mail
        if await self.user_repo.read_by_email(dto.email):
            raise ExistingEmailException(f"Email {dto.email} already exists.")

        # Hash the password using injected function
        hashed_password = self.password_hasher(dto.password)

        #Construct the user entity based on role
        if dto.role == RoleEnum.CLIENT:
            
            if dto.age is None or (dto.age < 14 or dto.age > 100):
                raise InvalidUserAge(dto.age)
            if dto.site_id is None:
                raise PersistenceException("Site ID must be provided for clients.")
            if self.site_repo.read_by_id(dto.site_id) is None:
                raise PersistenceException(f"Site with ID {dto.site_id} does not exist.")  
            
            user_entity = Client(id=None, name=dto.name, email=dto.email, password_hash=hashed_password, role= RoleEnum.CLIENT, age=dto.age, site_id=dto.site_id)
        
        elif dto.role == RoleEnum.TRAINER:
            if dto.specialty is None:
                raise PersistenceException("Specialty must be provided for trainers.")
            
            user_entity = Trainer(id=None,
                                name=dto.name, email=dto.email, password_hash=hashed_password, role= RoleEnum.TRAINER, specialty=TrainerSpecialtyEnum(dto.specialty)) 
        else:
            user_entity = User(id=None, name=dto.name, email=dto.email, password_hash=hashed_password, role= RoleEnum.ADMIN)

        # Save the user entity to the repository
        saved_user = await self.user_repo.save(user_entity)

        # Return the output DTO
        return UserOutputDTO(id= cast(int, saved_user.id), name=saved_user.name, email=saved_user.email, role=saved_user.role, specialty=getattr(saved_user, 'specialty', None), age=getattr(saved_user, 'age', None), site_id=getattr(saved_user, 'site_id', None))
