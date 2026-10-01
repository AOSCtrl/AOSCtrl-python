class OrchApiError(Exception):
    def __init__(self, status_code, code, message, details=None, request_id=None, correlation_id=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.details = details
        self.request_id = request_id
        self.correlation_id = correlation_id
