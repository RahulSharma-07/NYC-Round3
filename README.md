# NYC-Round3
# EchoX

AI-powered voice/text computer controller. Uses Google Gemini to interpret natural language commands and control your computer via PyAutoGUI.

## Demo

## Features

- Voice or text input — speak commands or type them
- AI-powered command interpretation — Gemini figures out intent and breaks it into steps
- Multilingual support — works in English and Hindi, so you can give commands in either language
- Dynamic element detection — finds UI elements by describing them (Gemini vision)
- Cross-platform — works on macOS & Windows
- Fallback search strategies — keyboard shortcuts, tab navigation, area clicks

## Quick Start

```bash
# Install
pip install pc-use

# Set your Gemini API key
export GEMINI_API_KEY="your_key_here"

# Run (voice mode)
pc-use

# Run (text mode)
pc-use --text
```

## Usage

### Voice mode
```bash
pc-use
```

### Text mode
```bash
pc-use --text
```

### Language

EchoX supports both English and Hindi commands out of the box. Just speak or type in whichever language you prefer — no extra flag needed, Gemini detects and interprets the language automatically.

```bash
# English
"open chrome"

# Hindi
"chrome kholo"
```

### Custom API key
```bash
pc-use --api-key "your_key_here"
# or
GEMINI_API_KEY="your_key_here" pc-use
```

### Show version
```bash
pc-use --version
```

## Example Commands

| You say | What it does |
|---|---|
| "open chrome" | Launches Google Chrome |
| "chrome kholo" | Launches Google Chrome (Hindi) |
| "search for cats on google" | Opens browser, types query, presses enter |
| "google par cats search karo" | Opens browser, types query, presses enter (Hindi) |
| "open youtube and search cats" | Opens YouTube, uses `/`, types query, searches |
| "scroll down" | Scrolls page down |
| "neeche scroll karo" | Scrolls page down (Hindi) |
| "make the text bigger" | Sends zoom-in hotkey |
| "close this window" | Sends Cmd+Q (macOS) / Alt+F4 (Windows) |
| "take a screenshot" | Triggers screenshot shortcut |
| "click the blue button" | Finds element via AI vision, clicks it |

## How It Works

1. User speaks or types a command in English or Hindi
2. Gemini interprets the command and returns a structured plan (JSON steps)
3. For click/find actions, Gemini vision analyzes a screenshot to locate UI elements
4. PyAutoGUI executes the steps (clicks, keystrokes, hotkeys, app launches)

## Requirements

- Python 3.10+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
- Voice mode only: microphone + PyAudio (`pip install pc-use[voice]`)

## Development

Clone the repo and install in editable mode:

```bash
git clone https://github.com/your-username/echox.git
cd echox
pip install -e ".[voice]"
```

Run the test suite:

```bash
pytest
```

Contributions are welcome — open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
