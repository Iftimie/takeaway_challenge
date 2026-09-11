from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.auth.schemas import UserResponse
from app.auth.service import password_hasher
from app.db import get_session
from app.models import Restaurant, StaffAssignment, User
from app.staff.schemas import AssignmentResponse, StaffCreate

router = APIRouter(prefix="/staff", tags=["staff"], dependencies=[Depends(require_admin)])


@router.post("", response_model=UserResponse, status_code=201)
def create_staff(
    data: StaffCreate, session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
    user = User(
        email=str(data.email), name=data.name, role="staff",
        password_hash=password_hasher.hash(data.password.get_secret_value()),
    )
    session.add(user)
    try:
        session.flush()
        response = UserResponse.model_validate(user)
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "uq_users_email":
            raise HTTPException(409, "Email already registered") from None
        raise
    return response


@router.post("/{staff_id}/restaurants/{restaurant_id}", status_code=201)
def assign_restaurant(
    staff_id: Annotated[int, Path(ge=1, le=2147483647)],
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    session: Annotated[Session, Depends(get_session)],
) -> AssignmentResponse:
    staff = session.get(User, staff_id)
    if staff is None:
        raise HTTPException(404, "Staff user not found")
    if staff.role != "staff":
        raise HTTPException(409, "User is not staff")
    if session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(404, "Restaurant not found")
    session.add(StaffAssignment(staff_id=staff_id, restaurant_id=restaurant_id))
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "pk_staff_assignments":
            raise HTTPException(409, "Staff already assigned to restaurant") from None
        raise
    return AssignmentResponse(staff_id=staff_id, restaurant_id=restaurant_id)
