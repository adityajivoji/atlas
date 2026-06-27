


class Error(Exception):
    message: str
    status_code: int
    details: dict
    success: bool
    
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict = {}
        ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details
        self.success = True if 200 <= self.status_code < 300 else False
        