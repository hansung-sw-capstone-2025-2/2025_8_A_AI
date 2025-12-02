from typing import Optional


class PanelSearchException(Exception):
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class QueryParsingError(PanelSearchException):
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Query parsing failed: {reason}",
            code="QUERY_PARSING_ERROR",
            status_code=400,
            details={"query": query, "reason": reason}
        )


class DatabaseError(PanelSearchException):
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database error during {operation}: {reason}",
            code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation, "reason": reason}
        )


class LLMError(PanelSearchException):
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"LLM error during {operation}: {reason}",
            code="LLM_ERROR",
            status_code=500,
            details={"operation": operation, "reason": reason}
        )


class NotFoundError(PanelSearchException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )


class ValidationError(PanelSearchException):
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation error for {field}: {reason}",
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, "reason": reason}
        )
