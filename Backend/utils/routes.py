from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.endpoints import openai,appointment

router = APIRouter()

@router.get("/health")
async def default_route():
    return JSONResponse(status_code=200, content={"response":"Healthy"})

router.include_router(openai.router, prefix="/api")
router.include_router(appointment.router, prefix="/api")

@router.route("/{full_path:path}")
async def catch_all(full_path: str):
    return JSONResponse(status_code=404, content={"status": False, "errors": [{"message": "Please provide a valid URL"}]})