"""
Task management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import (
    Task as TaskSchema,
    TaskCreate,
    TaskUpdate,
    TaskWithProject
)

router = APIRouter()


@router.get("/", response_model=List[TaskWithProject])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's tasks with filtering and pagination."""
    query = select(Task).join(Project).where(Project.owner_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    
    # Convert to response format
    task_responses = []
    for task in tasks:
        task_dict = task.__dict__.copy()
        task_dict['project_name'] = task.project.name if task.project else None
        task_dict['assigned_username'] = task.assigned_user.username if task.assigned_user else None
        task_responses.append(TaskWithProject(**task_dict))
    
    return task_responses


@router.get("/{task_id}", response_model=TaskWithProject)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task by ID."""
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(
            and_(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task_dict = task.__dict__.copy()
    task_dict['project_name'] = task.project.name if task.project else None
    task_dict['assigned_username'] = task.assigned_user.username if task.assigned_user else None
    
    return TaskWithProject(**task_dict)


@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    project_id: int = Query(..., description="Project ID for the task"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task in a project."""
    # Verify project exists and user owns it
    result = await db.execute(
        select(Project).where(
            and_(
                Project.id == project_id,
                Project.owner_id == current_user.id
            )
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify assigned user exists if provided
    if task_data.assigned_to:
        result = await db.execute(
            select(User).where(User.id == task_data.assigned_to)
        )
        assigned_user = result.scalar_one_or_none()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not found"
            )
    
    # Create task
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        project_id=project_id,
        assigned_to=task_data.assigned_to,
        due_date=task_data.due_date
    )
    
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    return db_task


@router.put("/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(
            and_(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify assigned user exists if provided
    if task_update.assigned_to:
        result = await db.execute(
            select(User).where(User.id == task_update.assigned_to)
        )
        assigned_user = result.scalar_one_or_none()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not found"
            )
    
    # Update task fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(
            and_(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    await db.delete(task)
    await db.commit()
    
    return None


@router.get("/project/{project_id}/tasks", response_model=List[TaskWithProject])
async def get_project_tasks(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    task_status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks for a specific project."""
    # Verify project exists and user owns it
    result = await db.execute(
        select(Project).where(
            and_(
                Project.id == project_id,
                Project.owner_id == current_user.id
            )
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Build query
    query = select(Task).where(Task.project_id == project_id)
    
    if task_status:
        query = query.where(Task.status == task_status)
    if priority:
        query = query.where(Task.priority == priority)
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    
    # Convert to response format
    task_responses = []
    for task in tasks:
        task_dict = task.__dict__.copy()
        task_dict['project_name'] = project.name
        task_dict['assigned_username'] = task.assigned_user.username if task.assigned_user else None
        task_responses.append(TaskWithProject(**task_dict))
    
    return task_responses

