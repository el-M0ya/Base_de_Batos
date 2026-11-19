"""DTOs for the site management use cases.

All DTOs are immutable: use cases receive plain data and return new values
instead of mutating what the caller passed in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.domain.entities.site import Site
from app.domain.exceptions.domain_exceptions import InvalidDomainValue


@dataclass(frozen=True)
class CreateSiteInputDTO:
    """Data required to create a new gym site."""

    actor: ActorDTO
    name: str
    address: str

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        if not isinstance(self.address, str) or not self.address.strip():
            raise InvalidDomainValue("address", self.address, "a non-empty address")


@dataclass(frozen=True)
class SiteOutputDTO:
    """Flat representation of a site returned to the caller."""

    id_site: int
    name: str
    address: str
    created_at: datetime

    @classmethod
    def from_entity(cls, site: Site) -> "SiteOutputDTO":
        """Map a domain entity to the application output DTO."""
        if site.id_site is None:
            raise InvalidDomainValue(
                "id_site", site.id_site, "a persisted site"
            )
        return cls(
            id_site=site.id_site,
            name=site.name,
            address=site.address,
            created_at=site.created_at,
        )


@dataclass(frozen=True)
class UpdateSiteInputDTO:
    """Data accepted to update an existing site."""

    actor: ActorDTO
    id_site: int
    name: Optional[str] = None
    address: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_site, int)
            or isinstance(self.id_site, bool)
            or self.id_site <= 0
        ):
            raise InvalidDomainValue(
                "id_site", self.id_site, "an integer greater than 0"
            )
        if self.name is not None and (
            not isinstance(self.name, str) or not self.name.strip()
        ):
            raise InvalidDomainValue("name", self.name, "a non-empty name")
        if self.address is not None and (
            not isinstance(self.address, str) or not self.address.strip()
        ):
            raise InvalidDomainValue("address", self.address, "a non-empty address")


@dataclass(frozen=True)
class DeactivateSiteInputDTO:
    """Data required to deactivate an existing site."""

    actor: ActorDTO
    id_site: int

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
        if (
            not isinstance(self.id_site, int)
            or isinstance(self.id_site, bool)
            or self.id_site <= 0
        ):
            raise InvalidDomainValue(
                "id_site", self.id_site, "an integer greater than 0"
            )


@dataclass(frozen=True)
class ListSitesInputDTO:
    """Filters accepted when listing sites."""

    actor: ActorDTO

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorDTO):
            raise InvalidDomainValue("actor", self.actor, "an ActorDTO instance")
