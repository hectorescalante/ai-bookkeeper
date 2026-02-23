"""Outlook OAuth API routes."""
import json
from datetime import datetime
from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.adapters.email import OutlookOAuthManager
from backend.adapters.persistence.database import get_db
from backend.adapters.persistence.models.configuration import OutlookOAuthStateModel
from backend.config.dependencies import (
    get_outlook_oauth_manager,
    get_settings_repository,
)
from backend.domain.entities.configuration import Settings
from backend.ports.output.repositories import SettingsRepository

router = APIRouter(prefix="/api/settings/outlook", tags=["outlook"])


class OutlookConnectResponse(BaseModel):
    """Response with URL to start Outlook OAuth in browser."""

    authorization_url: str


class OutlookDisconnectResponse(BaseModel):
    """Response after Outlook disconnect operation."""

    outlook_configured: bool


@router.get("/connect", response_model=OutlookConnectResponse, status_code=200)
def connect_outlook(
    oauth_manager: Annotated[OutlookOAuthManager, Depends(get_outlook_oauth_manager)],
    db: Session = Depends(get_db),
) -> OutlookConnectResponse:
    """Create Outlook OAuth authorization URL."""
    auth_session = oauth_manager.start_authorization()
    _cleanup_expired_states(db)
    db.merge(
        OutlookOAuthStateModel(
            state=auth_session.state,
            flow_payload=json.dumps(auth_session.flow_payload),
            expires_at=auth_session.expires_at,
            created_at=datetime.now(),
        )
    )
    db.commit()
    return OutlookConnectResponse(authorization_url=auth_session.authorization_url)


@router.get("/callback", response_class=HTMLResponse, status_code=200)
def outlook_callback(
    state: Annotated[str | None, Query()] = None,
    code: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
    oauth_manager: OutlookOAuthManager = Depends(get_outlook_oauth_manager),
    settings_repo: SettingsRepository = Depends(get_settings_repository),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Handle Outlook OAuth callback and persist refresh token."""
    params: dict[str, str] = {}
    if state is not None:
        params["state"] = state
    if code is not None:
        params["code"] = code
    if error is not None:
        params["error"] = error
    if error_description is not None:
        params["error_description"] = error_description

    try:
        if not state:
            raise ValueError("Missing OAuth state in callback")

        _cleanup_expired_states(db)
        state_row = (
            db.query(OutlookOAuthStateModel)
            .filter(OutlookOAuthStateModel.state == state)
            .first()
        )
        if state_row is None:
            raise ValueError("OAuth session expired. Start connect again.")
        if state_row.expires_at < datetime.now():
            db.delete(state_row)
            db.commit()
            raise ValueError("OAuth session expired. Start connect again.")

        try:
            flow_payload = json.loads(state_row.flow_payload)
        except json.JSONDecodeError as json_exc:
            db.delete(state_row)
            db.commit()
            raise ValueError("Invalid OAuth state. Start connect again.") from json_exc

        if not isinstance(flow_payload, dict):
            db.delete(state_row)
            db.commit()
            raise ValueError("Invalid OAuth state. Start connect again.")

        # Enforce one-time use of state token.
        db.delete(state_row)
        db.commit()

        refresh_token = oauth_manager.complete_authorization(flow_payload, params)
        settings = settings_repo.get() or Settings.create()
        settings.set_outlook_configured(True, refresh_token=refresh_token)
        settings_repo.save(settings)
        return HTMLResponse(
            content=(
                "<html><body><h2>Outlook connected successfully.</h2>"
                "<p>You can close this tab and return to AI Bookkeeper.</p></body></html>"
            ),
            status_code=200,
        )
    except ValueError as exc:
        safe_error = escape(str(exc))
        return HTMLResponse(
            content=(
                "<html><body><h2>Outlook connection failed.</h2>"
                f"<p>{safe_error}</p><p>You can close this tab and retry from the app.</p>"
                "</body></html>"
            ),
            status_code=400,
        )


@router.post("/disconnect", response_model=OutlookDisconnectResponse, status_code=200)
def disconnect_outlook(
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> OutlookDisconnectResponse:
    """Disconnect Outlook integration and clear stored refresh token."""
    settings = settings_repo.get() or Settings.create()
    settings.disconnect_outlook()
    settings_repo.save(settings)
    return OutlookDisconnectResponse(outlook_configured=settings.outlook_configured)


def _cleanup_expired_states(db: Session) -> None:
    db.query(OutlookOAuthStateModel).filter(
        OutlookOAuthStateModel.expires_at < datetime.now()
    ).delete()
    db.commit()
