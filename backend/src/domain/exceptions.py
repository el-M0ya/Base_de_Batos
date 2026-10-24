from typing import Optional


class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass

# USER EXCEPTIONS
class InvalidEmailException(DomainException):
    """Raised when an invalid email is provided."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Invalid email provided: {email}")
    pass

class ExistingEmailException(DomainException):
    """Raised when an email already exists in the system."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email already exists: {email}")
    pass

class InvalidUserAge(DomainException):
    """Raised when an invalid user age is provided."""
    
    def __init__(self, age: Optional[int] = None):
        self.age = age
        super().__init__(f"Invalid user age provided: {age}")
    pass

# DB EXCEPTIONS
class PersistenceException(DomainException):
    """Raised when a persistence operation fails."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Persistence operation failed: {message}")
    pass

# SITE EXCEPTIONS