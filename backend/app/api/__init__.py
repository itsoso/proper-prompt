"""API routes"""
from fastapi import APIRouter
from app.api import groups, prompts, analysis, evaluations, api_keys, integrations

api_router = APIRouter()

api_router.include_router(groups.router, prefix="/groups", tags=["Groups"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])

