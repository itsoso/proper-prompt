"""Pytest configuration and fixtures"""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app


# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_group_data():
    """Sample group data for tests"""
    return {
        "external_id": "test_group_001",
        "name": "Test Investment Group",
        "type": "investment",
        "description": "A test investment group",
        "member_count": 50,
    }


@pytest.fixture
def sample_prompt_template_data():
    """Sample prompt template data for tests"""
    return {
        "name": "Test Analysis Template",
        "description": "A test template for analysis",
        "group_type": "investment",
        "time_granularity": "daily",
        "style": "analytical",
        "system_prompt": "You are a professional analyst.",
        "user_prompt_template": "Analyze: {chat_content}",
        "required_variables": ["chat_content"],
        "optional_variables": ["member_filter"],
    }


@pytest.fixture
def sample_chat_content():
    """Sample chat content for tests"""
    return """
[2024-01-15 09:00] 张三: 大家好，今天市场怎么看？
[2024-01-15 09:02] 李四: 我觉得科技股有机会
[2024-01-15 09:05] 王五: 同意，特别是AI相关的
[2024-01-15 09:10] 张三: 具体看哪些标的呢？
[2024-01-15 09:15] 李四: 我比较看好NVIDIA和Microsoft
[2024-01-15 09:20] 赵六: 风险也不小，注意仓位控制
"""

