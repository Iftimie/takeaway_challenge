from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.restaurants.router import router as restaurants_router
from app.staff.router import router as staff_router
from app.menu.router import router as menu_router

app = FastAPI(title="Takeaway Service")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurants_router)
app.include_router(staff_router)
app.include_router(menu_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    # FastAPI's default errors include input values, which can contain passwords.
    return JSONResponse(
        status_code=422,
        content={"detail": [
            {key: item[key] for key in ("loc", "msg", "type")}
            for item in error.errors()
        ]},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
