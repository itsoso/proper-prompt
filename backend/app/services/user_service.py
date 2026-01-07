"""User service for authentication and user management"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.get_by_username(username)
        
        if not user:
            logger.warning("login_failed_user_not_found", username=username)
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning("login_failed_invalid_password", username=username)
            return None
        
        if not user.is_active:
            logger.warning("login_failed_user_inactive", username=username)
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        logger.info("user_authenticated", user_id=user.id, username=username)
        return user
    
    async def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        is_superuser: bool = False,
    ) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_superuser=is_superuser,
            is_active=True,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("user_created", user_id=user.id, username=username)
        return user
    
    async def update_password(self, user: User, new_password: str) -> User:
        """Update user password"""
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info("password_updated", user_id=user.id)
        return user
    
    async def ensure_admin_exists(self) -> User:
        """Ensure default admin user exists"""
        admin = await self.get_by_username("admin")
        
        if not admin:
            admin = await self.create_user(
                username="admin",
                password="admin123",  # 默认密码，首次登录后应修改
                email="admin@example.com",
                full_name="系统管理员",
                is_superuser=True,
            )
            logger.info("default_admin_created", user_id=admin.id)
        
        return admin

