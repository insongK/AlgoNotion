class AppError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class BadRequestError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(400, detail)


class TooManyRequestsError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(429, detail)


class BadGatewayError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(502, detail)


class ServiceUnavailableError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(503, detail)
