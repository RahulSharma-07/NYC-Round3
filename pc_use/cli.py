import argparse
import sys

from pc_use.config import Config
from pc_use.controller import VoiceComputerController
from pc_use.logger import setup_logger

logger = setup_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-Powered Voice/Text Computer Controller",
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (default: GEMINI_API_KEY env var)",
        default=None,
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Use text input instead of voice",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Use voice input (default if no flag given)",
    )
    parser.add_argument(
        "--groq",
        action="store_true",
        help="Use Groq instead of Gemini",
    )
    parser.add_argument(
        "--groq-api-key",
        default=None,
        help="Groq API key (default: GROQ_API_KEY env var)",
    )
    parser.add_argument(
        "--groq-model",
        default=None,
        help="Groq text model name (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--groq-vision-model",
        default=None,
        help="Groq vision model name (default: meta-llama/llama-4-scout-17b-16e-instruct)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from pc_use import __version__

        print(f"pc-use v{__version__}")
        return

    use_voice: bool = True
    if args.text:
        use_voice = False
    elif args.voice:
        use_voice = True

    config = Config(
        api_key=args.api_key,
        use_voice=use_voice,
        backend="groq" if args.groq else "gemini",
        groq_api_key=args.groq_api_key,
        groq_model=args.groq_model,
        groq_vision_model=args.groq_vision_model,
    )

    if config.backend == "groq" and not config.groq_api_key:
        logger.error(
            "Groq API key is required. Set GROQ_API_KEY env var, pass --groq-api-key, "
            "or drop --groq to use Gemini instead"
        )
        sys.exit(1)

    # AQ. keys are OAuth2 tokens — they don't work with the Gemini REST API.
    # Auto-switch to Groq if available.
    if config.backend == "gemini" and config.api_key.startswith("AQ."):
        if config.groq_api_key:
            logger.warning(
                "GEMINI_API_KEY starts with 'AQ.' (OAuth2 token) which is not supported "
                "by the Gemini REST API. Auto-switching to Groq backend."
            )
            config.backend = "groq"
        else:
            logger.error(
                "GEMINI_API_KEY starts with 'AQ.' which is not supported. "
                "Set GROQ_API_KEY and PC_USE_BACKEND=groq to use Groq instead."
            )
            sys.exit(1)

    if config.backend == "gemini" and not config.api_key:
        logger.error(
            "Gemini API key is required. Set GEMINI_API_KEY env var, pass --api-key, "
            "or use --groq for Groq instead"
        )
        sys.exit(1)

    print(f"Detected OS: {sys.platform}  |  Backend: {config.backend.capitalize()}")

    if use_voice and sys.platform == "darwin":
        print("\nMac Setup Requirements for Voice Commands:")
        print("1. Grant microphone access in System Preferences > Security & Privacy > Privacy > Microphone")
        print("2. Grant accessibility access in System Preferences > Security & Privacy > Privacy > Accessibility")
        print("3. Install Xcode command line tools: xcode-select --install\n")
    elif sys.platform == "darwin":
        print("\nMac Setup Requirements:")
        print("1. Grant accessibility access in System Preferences > Security & Privacy > Privacy > Accessibility")
        print("2. Install Xcode command line tools: xcode-select --install\n")

    controller = VoiceComputerController(config)
    controller.run()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
