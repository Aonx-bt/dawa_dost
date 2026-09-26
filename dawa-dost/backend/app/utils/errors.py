"""Shared HTTP error helpers that map internal failures to patient-friendly messages."""
from fastapi import HTTPException


def not_found(entity: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{entity} not found")


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def extraction_failed(reason: str) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={
            "message": "We couldn't read this prescription clearly.",
            "hint": "Please upload a clearer photo or enter the medicine details manually.",
            "reason": reason,
        },
    )


def upstream_failure(service: str, reason: str) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail={
            "message": f"{service} is temporarily unavailable. Please try again shortly.",
            "reason": reason,
        },
    )
