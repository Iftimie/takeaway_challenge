from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_session
from app.menu.schemas import MenuItemCreate, MenuItemResponse, MenuItemUpdate
from app.models import MenuItem, Restaurant, StaffAssignment, User

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu-items", tags=["menu"])


def require_assigned_staff(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    if user.role != "staff":
        raise HTTPException(403, "Assigned staff access required")
    if session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(404, "Restaurant not found")
    if session.get(StaffAssignment, (user.id, restaurant_id)) is None:
        raise HTTPException(403, "Assigned staff access required")


@router.get("", response_model=list[MenuItemResponse])
def list_menu_items(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[MenuItem]:
    if session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(404, "Restaurant not found")
    statement = (
        select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)
        .order_by(MenuItem.id).limit(limit).offset(offset)
    )
    return list(session.scalars(statement))


@router.post("", response_model=MenuItemResponse, status_code=201,
             dependencies=[Depends(require_assigned_staff)])
def create_menu_item(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    data: MenuItemCreate,
    session: Annotated[Session, Depends(get_session)],
) -> MenuItemResponse:
    item = MenuItem(
        restaurant_id=restaurant_id, name=data.name,
        price=data.price, available=data.available,
    )
    session.add(item)
    session.flush()
    # Read the stored NUMERIC value so the response has two decimal places.
    session.refresh(item)
    response = MenuItemResponse.model_validate(item)
    session.commit()
    return response


@router.patch("/{item_id}", response_model=MenuItemResponse,
              dependencies=[Depends(require_assigned_staff)])
def update_menu_item(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    item_id: Annotated[int, Path(ge=1, le=2147483647)],
    data: MenuItemUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> MenuItemResponse:
    item = session.scalar(select(MenuItem).where(
        MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id,
    ))
    if item is None:
        raise HTTPException(404, "Menu item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    session.flush()
    session.refresh(item)
    response = MenuItemResponse.model_validate(item)
    session.commit()
    return response
