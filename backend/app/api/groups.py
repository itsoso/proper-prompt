"""Group management API routes"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.group import Group, GroupType
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupListResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=GroupListResponse)
async def list_groups(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    type: Optional[GroupType] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all groups with pagination and filtering"""
    query = select(Group).where(Group.is_active == True)
    
    if type:
        query = query.where(Group.type == type)
    if search:
        query = query.where(Group.name.ilike(f"%{search}%"))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    groups = result.scalars().all()
    
    logger.info("list_groups", page=page, size=size, total=total)
    
    return GroupListResponse(
        items=[GroupResponse.model_validate(g) for g in groups],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new group"""
    # Check for existing external_id
    existing = await db.execute(
        select(Group).where(Group.external_id == group_data.external_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group with this external_id already exists")
    
    group = Group(**group_data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    logger.info("group_created", group_id=group.id, name=group.name)
    return GroupResponse.model_validate(group)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a group by ID"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return GroupResponse.model_validate(group)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a group"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    
    logger.info("group_updated", group_id=group_id)
    return GroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a group"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group.is_active = False
    await db.commit()
    
    logger.info("group_deleted", group_id=group_id)


@router.get("/types/list", response_model=List[dict])
async def list_group_types():
    """List all available group types"""
    return [
        {"value": gt.value, "label": gt.name.replace("_", " ").title()}
        for gt in GroupType
    ]

