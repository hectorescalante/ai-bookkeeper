"""Use case for configuring application settings."""

from backend.application.dtos import ConfigureSettingsRequest, SettingsResponse
from backend.domain.entities.configuration import Settings
from backend.ports.output.repositories import SettingsRepository


class ConfigureSettingsUseCase:
    """Configure or update application settings."""

    def __init__(self, settings_repo: SettingsRepository):
        self.settings_repo = settings_repo

    def execute(self, request: ConfigureSettingsRequest) -> SettingsResponse:
        """Execute the use case."""
        # Get existing or create new
        settings = self.settings_repo.get()

        if not settings:
            settings = Settings.create()

        # Update fields if provided
        if request.gemini_api_key is not None:
            settings.set_api_key(request.gemini_api_key)

        if request.default_export_path is not None:
            settings.default_export_path = request.default_export_path

        if request.extraction_prompt is not None:
            settings.update_extraction_prompt(request.extraction_prompt)

        self.settings_repo.save(settings)

        return SettingsResponse(
            id=settings.id,
            has_api_key=settings.has_api_key,
            outlook_configured=settings.outlook_configured,
            default_export_path=settings.default_export_path,
            extraction_prompt=settings.extraction_prompt,
        )

    def get_settings(self) -> SettingsResponse | None:
        """Get current application settings."""
        settings = self.settings_repo.get()

        if not settings:
            return None

        return SettingsResponse(
            id=settings.id,
            has_api_key=settings.has_api_key,
            outlook_configured=settings.outlook_configured,
            default_export_path=settings.default_export_path,
            extraction_prompt=settings.extraction_prompt,
        )
