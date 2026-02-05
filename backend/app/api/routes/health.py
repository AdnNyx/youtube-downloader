from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health():
    return {"success": True, "message": "API is running"}
