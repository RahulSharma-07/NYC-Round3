import argparse
import sys

from pc_use.config import Config
from pc_use.controller import VoiceComputerController
from pc_use.logger import setup_logger

logger = setup_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-Powered Voice/Text Computer Controller (Groq backend)",
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
        "--groq-api-key",
        default=None,
        help="Groq API key (default: GROQ_API_KEY env var)",
    )
    parser.add_argument(
        "--groq-model",
        default=None,
        help="Groq text model (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--groq-vision-model",
        default=None,
        help="Groq vision model (default: meta-llama/llama-4-scout-17b-16e-instruct)",
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
        use_voice=use_voice,
        groq_api_key=args.groq_api_key,
        groq_model=args.groq_model,
        groq_vision_model=args.groq_vision_model,
    )

    if not config.groq_api_key:
        logger.error(
            "Groq API key is required. Set GROQ_API_KEY in your .env file "
            "or pass --groq-api-key."
        )
        sys.exit(1)

    print(f"Detected OS: {sys.platform}  |  Backend: Groq")

    if use_voice and sys.platform == "darwin":
        print("\nMac Setup Requirements for Voice Commands:")
        print("1. Grant microphone access in System Preferences > Security & Privacy > Microphone")
        print("2. Grant accessibility access in System Preferences > Security & Privacy > Accessibility")
        print("3. Install Xcode command line tools: xcode-select --install\n")
    elif sys.platform == "darwin":
        print("\nMac Setup Requirements:")
        print("1. Grant accessibility access in System Preferences > Security & Privacy > Accessibility")
        print("2. Install Xcode command line tools: xcode-select --install\n")

    controller = VoiceComputerController(config)
    controller.run()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
