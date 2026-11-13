from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Site:
    name: str
    address: str
    id_site: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("The name of the site can not be empty.")
        if not self.address or not self.address.strip():
            raise ValueError("The address of the site can not be empty.")