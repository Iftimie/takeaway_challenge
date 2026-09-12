from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.restaurants.router import router as restaurants_router
from app.staff.router import router as staff_router
from app.menu.router import router as menu_router
from app.orders.router import router as orders_router
from app.orders.staff_router import router as staff_orders_router
from app.request_logging import RequestLoggingMiddleware

app = FastAPI(title="Takeaway Service")
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurants_router)
app.include_router(staff_router)
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(staff_orders_router)
app.mount("/ui", StaticFiles(directory=Path(__file__).parent / "ui" / "dist", html=True, check_dir=False), name="ui")


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
