"""
Task Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for task creation."""
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for task updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskInDB(TaskBase):
    """Schema for task in database."""
    id: int
    project_id: int
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Task(TaskInDB):
    """Schema for task response."""
    pass


class TaskWithProject(Task):
    """Schema for task with project information."""
    project_name: Optional[str] = None
    assigned_username: Optional[str] = None

