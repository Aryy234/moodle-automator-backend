"""
API V1 Module
"""
from fastapi import APIRouter
from app.api.v1 import courses, editor

# Router principal para v1
api_router = APIRouter(prefix="/v1")

# Incluir sub-routers
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(editor.router, prefix="/editor", tags=["Editor"])
