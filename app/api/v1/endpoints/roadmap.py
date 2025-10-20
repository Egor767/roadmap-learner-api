import uuid
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_roadmap_service
from app.core.handlers import router_handler
from app.schemas.roadmap import RoadMapResponse, RoadMapCreate, RoadMapUpdate, RoadMapFilters
from app.services.roadmap.service import RoadMapService

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


# -------------------------------------- GET ----------------------------------------------
@router.get("/",
            response_model=List[RoadMapResponse],
            status_code=status.HTTP_200_OK)
@router_handler
async def get_all_roadmaps(
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    return await roadmap_service.get_all_roadmaps()


@router.get("/{roadmap_id}",
            response_model=RoadMapResponse,
            status_code=status.HTTP_200_OK)
@router_handler
async def get_roadmap(
    user_id: uuid.UUID,  # = Depends(get_current_user) / access_token.user_id
    roadmap_id: uuid.UUID,
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    return await roadmap_service.get_user_roadmap(user_id, roadmap_id)


@router.get("/user/{user_id}/filter",
            response_model=List[RoadMapResponse],
            status_code=status.HTTP_200_OK)
@router_handler
async def get_user_roadmaps_by_filters(
    user_id: uuid.UUID,  # = Depends(get_current_user) / access_token.user_id
    filters: RoadMapFilters = Depends(),
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    return await roadmap_service.get_user_roadmaps_by_filters(user_id, filters)


# -------------------------------------- CREATE --------------------------------------
@router.post("/",
             response_model=RoadMapResponse,
             status_code=status.HTTP_201_CREATED)
@router_handler
async def create_roadmap(
    user_id: uuid.UUID,  # = Depends(get_current_user) / access_token.user_id
    roadmap_data: RoadMapCreate,
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    return await roadmap_service.create_roadmap(user_id, roadmap_data)


# -------------------------------------- DELETE --------------------------------------
@router.delete("/{roadmap_id}",
               status_code=status.HTTP_204_NO_CONTENT)
@router_handler
async def delete_roadmap(
    user_id: uuid.UUID,  # = Depends(get_current_user) / access_token.user_id
    roadmap_id: uuid.UUID,
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    await roadmap_service.delete_roadmap(user_id, roadmap_id)
    return {"road_id": str(roadmap_id), "status": "deleted"}


# -------------------------------------- UPDATE --------------------------------------
@router.patch("/{roadmap_id}",
              response_model=RoadMapResponse,
              status_code=status.HTTP_200_OK)
async def update_roadmap(
    user_id: uuid.UUID,  # = Depends(get_current_user) / access_token.user_id
    roadmap_id: uuid.UUID,
    roadmap_data: RoadMapUpdate,
    roadmap_service: RoadMapService = Depends(get_roadmap_service)
):
    return await roadmap_service.update_roadmap(user_id, roadmap_id, roadmap_data)

