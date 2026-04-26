from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from app.utils.env_manager import env_manager

router = APIRouter()

class SettingsUpdate(BaseModel):
    keys: Dict[str, str]

@router.get("/status")
async def get_setup_status():
    return {
        "is_complete": env_manager.is_setup_complete(),
        "configured_keys": [k for k, v in env_manager.get_keys().items() if v]
    }

@router.post("/update")
async def update_settings(data: SettingsUpdate):
    try:
        for key, value in data.keys.items():
            if value: # Only update if a value is provided
                env_manager.update_key(key, value)
        return {"status": "success", "message": "API keys updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: This is a placeholder, I'll need to register this router in main.py
