from fastapi import Request

from src.services import UsageService


def get_usage_service(request: Request) -> UsageService:
    return UsageService(
        client=request.app.state.client, calculator=request.app.state.calculator
    )
