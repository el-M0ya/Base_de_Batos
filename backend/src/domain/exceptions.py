class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass

class InvalidEmailException(DomainException):
    """Raised when an invalid email is provided."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Invalid email provided: {email}")
    pass

class InvalidUserAge(DomainException):
    """Raised when an invalid user age is provided."""
    
    def __init__(self, age: int):
        self.age = age
        super().__init__(f"Invalid user age provided: {age}")
    pass