
    
    
class ApiResponse(Exception):
    """Custom exception for API-style errors with structured info."""
    
    def __init__(self, 
                 message: str = "An error occurred", 
                 status_code: int = 500, 
                 error_code: str | None = None, 
                 details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert error to a JSON-friendly dict (like an API response)."""
        return {
            "success": True if 200 <= self.status_code < 300 else False,
            "message": self.message,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "details": self.details
        }
    
    def __str__(self):
        return f"[{self.status_code}] {self.error_code}: {self.message}"