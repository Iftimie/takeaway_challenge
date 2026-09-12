from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.db import get_session
from app.models import Restaurant
from app.restaurants.schemas import RestaurantCreate, RestaurantResponse

from app.payload_logging import PayloadLoggingRoute

router = APIRouter(prefix="/restaurants", tags=["restaurants"], route_class=PayloadLoggingRoute)


@router.get("", response_model=list[RestaurantResponse])
def list_restaurants(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[Restaurant]:
    statement = select(Restaurant).order_by(Restaurant.id).limit(limit).offset(offset)
    return list(session.scalars(statement))


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    session: Annotated[Session, Depends(get_session)],
) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


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
