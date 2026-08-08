import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".pc_use"
PREFS_FILE = CONFIG_DIR / "user_preferences.json"


class Config:
    def __init__(
        self,
        api_key: str | None = None,
        use_voice: bool | None = None,
        backend: str | None = None,
        groq_api_key: str | None = None,
        groq_model: str | None = None,
        groq_vision_model: str | None = None,
    ):
        load_dotenv(override=True)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        self.use_voice: bool = use_voice if use_voice is not None else True

        # Groq is the only supported backend
        self.backend: str = "groq"

        self.groq_api_key: str = (
            groq_api_key if groq_api_key is not None else os.getenv("GROQ_API_KEY", "")
        )
        self.groq_model: str = (
            groq_model if groq_model is not None
            else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        )
        self.groq_vision_model: str = (
            groq_vision_model if groq_vision_model is not None
            else os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        )

        self._preferences: dict[str, Any] = self._load_preferences()

    def _load_preferences(self) -> dict[str, Any]:
        defaults = {
            "voice_sensitivity": 0.7,
            "execution_speed": "normal",
            "confirmation_required": False,
            "learning_enabled": True,
            "proactive_suggestions": True,
            "preferred_applications": {},
            "custom_shortcuts": {},
            "automation_rules": [],
        }
        if PREFS_FILE.exists():
            try:
                with open(PREFS_FILE) as f:
                    return {**defaults, **json.load(f)}
            except (json.JSONDecodeError, OSError):
                return defaults
        return defaults

    def save_preferences(self) -> None:
        PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREFS_FILE, "w") as f:
            json.dump(self._preferences, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._preferences[key] = value
        self.save_preferences()
