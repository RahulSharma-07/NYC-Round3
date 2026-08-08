import base64
import json
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

import requests  # type: ignore[import-untyped]
from PIL import Image

from pc_use.logger import setup_logger

logger = setup_logger(__name__)


def _strip_json_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


COMMAND_PROMPT_TEMPLATE = """You are an intelligent computer automation assistant. Analyze this voice command and break it down into actionable steps: "{command}"

Your job is to understand ANY command and figure out how to execute it on a computer. Be creative and intelligent about interpreting user intent.

Respond with ONLY a JSON object in this exact format:
{{
    "steps": [
        {{
            "action": "click|type|scroll|drag|open|navigate|close|minimize|maximize|hotkey|wait",
            "target": "what to interact with or find on screen",
            "text_to_type": "text to type if needed",
            "direction": "up|down|left|right",
            "application": "name of application",
            "url": "full URL if navigating to a website",
            "hotkey": ["key1", "key2"],
            "wait_seconds": 2,
            "description": "what this step does"
        }}
    ],
    "confidence": confidence_level_0_to_1,
    "reasoning": "brief explanation of how you interpreted the command"
}}

CRITICAL RULES FOR WEB SEARCHES — always use direct URLs, never try to click search bars:
- "search X on youtube" -> use action "open" with url "https://www.youtube.com/results?search_query=X+encoded"
- "search X on google" -> use action "open" with url "https://www.google.com/search?q=X+encoded"
- "open youtube" -> use action "open" with url "https://www.youtube.com"
- "open google" -> use action "open" with url "https://www.google.com"
- ALWAYS URL-encode spaces as + in search queries

Examples of dynamic interpretation:
- "open chrome and search for cats on youtube" -> [{{"action":"open","url":"https://www.youtube.com/results?search_query=cats","application":"chrome","description":"Open YouTube search for cats"}}]
- "search for class 6 patterns on youtube" -> [{{"action":"open","url":"https://www.youtube.com/results?search_query=class+6+patterns","description":"Search YouTube for class 6 patterns"}}]
- "open bin" -> Find and open any application/folder named "bin"
- "go on chrome and launch a new tab" -> [open chrome, then press Ctrl+T for new tab]
- "close this window and open calculator" -> [close current window, open calculator]
- "make the text bigger" -> [use Ctrl + Plus hotkey]
- "scroll down and click the blue button" -> [scroll down, then look for blue button and click]

Be intelligent about:
1. Understanding context and user intent
2. Breaking complex commands into multiple steps
3. Using direct URLs for any web navigation — never try to click search bars
4. Figuring out what applications or UI elements the user means
5. Handling ambiguous commands by making reasonable assumptions

Operating System: {os}
"""

FIND_ELEMENT_PROMPT_TEMPLATE = """Look at this screenshot and find the {target}.

IMPORTANT INSTRUCTIONS:
- For search bars, look for text input fields, search icons, or "Search" text
- Look for rectangular input fields that are clickable
- If you see multiple similar elements, choose the most prominent one

Please respond with ONLY a JSON object in this exact format:
{{
    "found": true/false,
    "x": pixel_x_coordinate,
    "y": pixel_y_coordinate,
    "confidence": confidence_level_0_to_1,
    "description": "brief description of what you found"
}}

If you cannot find the {target}, set "found" to false.
The coordinates should be the center of the element you want to click.
Be very precise with coordinates - they must be clickable areas.
"""


def parse_json_response(text: str, context: str = "") -> dict[str, Any] | None:
    try:
        cleaned = _strip_json_markdown(text)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse %s JSON: %s", context, e)
        logger.debug("Raw text: %s", text)
        return None


class LLMBackend(ABC):
    @abstractmethod
    def interpret_command(self, command: str, is_mac: bool) -> dict[str, Any]:
        ...

    @abstractmethod
    def find_element(
        self, screenshot: Image.Image, target_description: str
    ) -> tuple[int, int] | None:
        ...


class GroqBackend(LLMBackend):
    """Backend powered by Groq's OpenAI-compatible chat completions API."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        vision_model: str = "llama-3.3-70b-versatile",
    ):
        self.api_key = api_key
        self.model = model
        self.vision_model = vision_model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _chat(self, messages: list[dict[str, Any]], model: str) -> str | None:
        try:
            resp = requests.post(
                self.API_URL,
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error("Groq request failed: %s", e)
            return None
        except (KeyError, IndexError) as e:
            logger.error("Unexpected Groq response shape: %s", e)
            return None

    def interpret_command(self, command: str, is_mac: bool) -> dict[str, Any]:
        os_name = "macOS" if is_mac else "Windows"
        prompt = COMMAND_PROMPT_TEMPLATE.format(command=command, os=os_name)

        text = self._chat(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        if not text:
            return {"steps": [], "confidence": 0}

        result = parse_json_response(text, "command")
        if result is None:
            return {"steps": [], "confidence": 0}

        logger.info("Groq reasoning: %s", result.get("reasoning", "No reasoning provided"))
        logger.info("Planned steps: %d", len(result.get("steps", [])))
        return result

    def find_element(
        self, screenshot: Image.Image, target_description: str
    ) -> tuple[int, int] | None:
        prompt = FIND_ELEMENT_PROMPT_TEMPLATE.format(target=target_description)

        try:
            buffer = BytesIO()
            screenshot.save(buffer, format="PNG")
            b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error("Failed to encode screenshot for Groq vision: %s", e)
            return None

        text = self._chat(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            model=self.vision_model,
        )
        if not text:
            return None

        result = parse_json_response(text, "vision")
        if result is None or not result.get("found", False):
            logger.warning("Groq could not find: %s", target_description)
            return None

        x, y = int(result["x"]), int(result["y"])
        confidence = result.get("confidence", 0)
        desc = result.get("description", "Found element")
        logger.info("Groq found: %s at (%d, %d) confidence=%.2f", desc, x, y, confidence)
        return (x, y)


def create_backend(config: Any) -> LLMBackend:
    """Always uses Groq."""
    return GroqBackend(
        api_key=config.groq_api_key,
        model=config.groq_model or "llama-3.3-70b-versatile",
        vision_model=config.groq_vision_model or "llama-3.3-70b-versatile",
    )
