from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class EnergyPlatformError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NoDataLoadedError(EnergyPlatformError):
    def __init__(self):
        super().__init__(
            "No dataset is loaded. Upload a CSV file or generate sample data first.",
            status_code=400,
        )


class InsufficientDataError(EnergyPlatformError):
    def __init__(self, required: int, actual: int):
        super().__init__(
            f"Insufficient data: need ≥ {required} records, got {actual}.",
            status_code=422,
        )


class InvalidScenarioError(EnergyPlatformError):
    def __init__(self, scenario: str):
        super().__init__(f"Unknown simulation scenario: '{scenario}'.", status_code=422)


class DeviceNotFoundError(EnergyPlatformError):
    def __init__(self, device_id: str):
        super().__init__(f"Device '{device_id}' not found in loaded dataset.", status_code=404)


# ── FastAPI exception handlers ────────────────────────────────────────────────
async def energy_platform_exception_handler(request: Request, exc: EnergyPlatformError):
    logger.warning(f"[{exc.status_code}] {exc.message} | path={request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Check server logs.", "status_code": 500},
    )
