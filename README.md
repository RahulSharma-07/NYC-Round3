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



## Development



## Usage

### Voice mode

### Text mode

### Custom API key

### Show version

## Example Commands

      |

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
