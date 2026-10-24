from typing import List, cast
from backend.src.domain.exceptions import PersistenceException
from src.domain.entities import Site 
from src.use_cases.dtos import SiteInputDTO, SiteOutputDTO 
from src.use_cases.ports.repositories import ISiteRepository

class SiteManagementUseCase:
    
    def __init__(self, site_repo: ISiteRepository):
        self.site_repo = site_repo

    async def create_site(self, dto: SiteInputDTO) -> SiteOutputDTO:
        new_site = Site(id = None, name=dto.name, address=dto.address)  # Create a new Site entity with no ID (to be assigned by the repository)

        saved_site = await self.site_repo.save(new_site) # Save the new site to the database
        
        if saved_site.id is None:
            raise PersistenceException("No ID assigned to the saved site.") 

        return SiteOutputDTO(id=saved_site.id, name=saved_site.name, address=saved_site.address)

    async def get_all_sites(self) -> List[SiteOutputDTO]:
        sites = await self.site_repo.read_all()
        return [SiteOutputDTO(id=site.id, name=site.name, address=site.address) for site in sites if site.id is not None]

    async def get_site_by_id(self, site_id: int) -> SiteOutputDTO:
        site = await self.site_repo.read_by_id(site_id)
        if site is None:
            raise PersistenceException(f"Site with ID {site_id} not found.")
        return SiteOutputDTO(id=cast(int, site.id), name=site.name, address=site.address)
    
    