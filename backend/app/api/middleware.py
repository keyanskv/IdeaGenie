from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.utils.env_manager import env_manager

async def setup_middleware(request: Request, call_next):
    # Skip setup check for static files and the setup API itself
    if request.url.path.startswith("/static") or request.url.path.startswith("/api/settings"):
        return await call_next(request)
    
    # If setup is not complete and we are not already on the setup page, redirect
    # (This logic will be more relevant once we have the frontend routes defined)
    if not env_manager.is_setup_complete():
        # In a real app, you might want to return a specific header or status
        # that the frontend uses to show a setup modal.
        pass

    return await call_next(request)
