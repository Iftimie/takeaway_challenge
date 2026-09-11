from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_session
from app.menu.schemas import MenuItemCreate, MenuItemResponse
from app.models import MenuItem, Restaurant, StaffAssignment, User

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu-items", tags=["menu"])


@router.post("", response_model=MenuItemResponse, status_code=201)
def create_menu_item(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    data: MenuItemCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> MenuItemResponse:
    if user.role != "staff":
        raise HTTPException(403, "Assigned staff access required")
    if session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(404, "Restaurant not found")
    if session.get(StaffAssignment, (user.id, restaurant_id)) is None:
        raise HTTPException(403, "Assigned staff access required")
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
