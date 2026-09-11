from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.db import get_session
from app.models import Restaurant
from app.restaurants.schemas import RestaurantCreate, RestaurantResponse

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post(
    "", response_model=RestaurantResponse, status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_restaurant(
    data: RestaurantCreate, session: Annotated[Session, Depends(get_session)]
) -> RestaurantResponse:
    restaurant = Restaurant(name=data.name, address=data.address)
    session.add(restaurant)
    session.flush()
    response = RestaurantResponse.model_validate(restaurant)
    session.commit()
    return response
