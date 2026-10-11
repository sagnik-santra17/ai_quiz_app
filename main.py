import logging
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.database import async_engine
from controllers.quiz_controller import router


# ---------- Logging Setup (Both File and Console) ---------- #
# 1. Create a root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 2. Define a common format for your logs
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 3. Create the File Handler (saves logs to the file)
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# 4. Create the Console Handler (streams logs live to the terminal)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# Turn down noise from external watchfiles library
logging.getLogger("watchfiles").setLevel(logging.WARNING)

# Now you can use this logger anywhere in this file
logger.info("Application starting up... (visible in both console and file)")



# ---------- Main FASTAPI App with Lifespan ---------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events: dispose database engine on exit."""
    yield
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="AI Quiz App",
    lifespan=lifespan,
    version="1.0.0",
    description="A quiz app powered by AI."
)


# ---------- CORS Middleware ---------- #
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    # Add production frontend domains here when deployed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Custom Middleware: Process Time Header ---------- #
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to every response (in seconds)."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ---------- Custom Middleware: Security Headers ---------- #
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add standard security headers to all responses."""
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com;"
    )

    return response


# ---------- Global Exception Handlers ---------- #
# HTTPException (401, 403, 404, 409, etc.)
@app.exception_handler(HTTPException)
async def global_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        logger.warning(
            f"Security Warning: Unauthorized {request.method} access to '{request.url.path}'. "
            f"Reason: {exc.detail}"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Catch-all for everything else (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# RequestValidationError (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())}
    )


# ------ Appliation routers ------- #
app.include_router(router) # -> Quiz controller



# ------ Root Endpoint ------ #
@app.get("/")
async def root():
    return {"message": "Welcome AI Quiz App!"}