# NYC-Round3
# EchoX

AI-powered voice/text computer controller. Uses Google Gemini to interpret natural language commands and control your computer via PyAutoGUI.

## Demo



## Features

- **Voice or text input** — speak commands or type them
- **AI-powered command interpretation** — Gemini figures out intent and breaks it into steps
- **Dynamic element detection** — finds UI elements by describing them (Gemini vision)
- **Cross-platform** — macOS & Windows
- **Fallback search strategies** — keyboard shortcuts, tab navigation, area clicks

## Quick Start
# Install
pip install pc-use

# Set your Gemini API key
export GEMINI_API_KEY="your_key_here"

# Run (voice mode)
pc-use

# Run (text mode)
pc-use --text


## Development



## Usage

### Voice mode
pc-use
### Text mode
pc-use --text

### Custom API key
pc-use --api-key "your_key_here"
# or
GEMINI_API_KEY="your_key_here" pc-use
### Show version

## Example Commands

    You say	What it does
"open chrome"	Launches Google Chrome
"search for cats on google"	Opens browser, types query, presses enter
"open youtube and search cats"	Opens YouTube, uses /, types query, searches
"scroll down"	Scrolls page down
"make the text bigger"	Sends zoom-in hotkey
"close this window"	Sends Cmd+Q (macOS) / Alt+F4 (Windows)
"take a screenshot"	Triggers screenshot shortcut
"click the blue button"	Finds element via AI vision, clicks it

## Requirements

- Python 3.10+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
- **Voice mode only:** microphone + PyAudio (`pip install pc-use[voice]`)

## How It Works

1. User speaks/types a command
2. Gemini interprets the command and returns a structured plan (JSON steps)
3. For click/find actions, Gemini vision analyses a screenshot to locate UI elements
4. PyAutoGUI executes the steps (clicks, keystrokes, hotkeys, app launches)

## License
