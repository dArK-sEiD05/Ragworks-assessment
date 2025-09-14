"""
Custom exceptions for the Task Management API.
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class TaskManagementException(Exception):
    """Base exception for Task Management API."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundError(TaskManagementException):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User with ID {user_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id}
        )


class ProjectNotFoundError(TaskManagementException):
    """Raised when a project is not found."""
    
    def __init__(self, project_id: int):
        super().__init__(
            message=f"Project with ID {project_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"project_id": project_id}
        )


class TaskNotFoundError(TaskManagementException):
    """Raised when a task is not found."""
    
    def __init__(self, task_id: int):
        super().__init__(
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id}
        )


class UnauthorizedError(TaskManagementException):
    """Raised when user is not authorized."""
    
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenError(TaskManagementException):
    """Raised when user doesn't have permission."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationError(TaskManagementException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


async def task_management_exception_handler(request, exc: TaskManagementException):
    """Exception handler for TaskManagementException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )

