import ctypes
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import pyautogui
import speech_recognition as sr
from PIL import Image

from pc_use.config import Config
from pc_use.llm import LLMBackend, create_backend
from pc_use.logger import setup_logger

logger = setup_logger(__name__)


class VoiceComputerController:
    def __init__(self, config: Config):
        self.config = config

        self.llm: LLMBackend = create_backend(config)

        if config.use_voice:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self._calibrate_microphone()

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        self.is_mac = platform.system() == "Darwin"
        self.is_windows = platform.system() == "Windows"

        self._setup_app_mappings()

        mode = "Voice" if config.use_voice else "Text"
        logger.info("%s Computer Controller initialized", mode)

    # name -> executable/command Windows can run directly (on PATH or a URI scheme)
    WINDOWS_APP_COMMANDS = {
        # browsers
        "chrome": "chrome.exe", "google chrome": "chrome.exe",
        "browser": "chrome.exe", "web browser": "chrome.exe",
        "internet browser": "chrome.exe", "internet": "chrome.exe",
        "firefox": "firefox.exe", "mozilla": "firefox.exe", "mozilla firefox": "firefox.exe",
        "edge": "msedge.exe", "microsoft edge": "msedge.exe",
        # editors / productivity
        "notepad": "notepad.exe", "text editor": "notepad.exe",
        "calculator": "calc.exe", "calc": "calc.exe",
        "explorer": "explorer.exe", "file explorer": "explorer.exe",
        "files": "explorer.exe", "this pc": "explorer.exe", "my computer": "explorer.exe",
        # shells
        "cmd": "cmd.exe", "command prompt": "cmd.exe",
        "terminal": "wt.exe", "powershell": "powershell.exe",
        # office
        "word": "winword.exe", "microsoft word": "winword.exe",
        "excel": "excel.exe", "microsoft excel": "excel.exe",
        "powerpoint": "powerpnt.exe", "microsoft powerpoint": "powerpnt.exe",
        # misc
        "paint": "mspaint.exe",
        "settings": "ms-settings:", "control panel": "control.exe",
        "task manager": "taskmgr.exe",
        "notepad++": "notepad++.exe",
        "vlc": "vlc.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "slack": "slack.exe",
        "zoom": "zoom.exe",
        "teams": "ms-teams:", "microsoft teams": "ms-teams:",
    }
    # fallback install locations for apps that aren't on PATH by default
    WINDOWS_APP_PATHS = {
        "chrome.exe": [
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
        ],
        "firefox.exe": [
            r"%ProgramFiles%\Mozilla Firefox\firefox.exe",
            r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe",
        ],
        "msedge.exe": [
            r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
            r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        ],
    }

    def _setup_app_mappings(self) -> None:
        if self.is_mac:
            self.common_apps = {
                "chrome": ["chrome", "google chrome", "browser"],
                "firefox": ["firefox", "mozilla"],
                "safari": ["safari"],
                "textedit": ["textedit", "text editor", "notepad"],
                "calculator": ["calculator", "calc"],
                "finder": ["finder", "files", "file manager"],
                "system preferences": ["system preferences", "settings", "preferences"],
                "terminal": ["terminal", "command prompt"],
                "pages": ["pages", "document"],
                "numbers": ["numbers", "spreadsheet"],
                "keynote": ["keynote", "presentation"],
                "spotlight": ["spotlight", "search"],
            }
        else:
            self.common_apps = {
                "chrome": ["chrome", "google chrome", "browser"],
                "firefox": ["firefox", "mozilla"],
                "notepad": ["notepad", "text editor"],
                "calculator": ["calculator", "calc"],
                "file explorer": ["explorer", "files", "file manager"],
                "settings": ["settings", "control panel"],
                "terminal": ["terminal", "command prompt", "cmd", "powershell"],
                "word": ["word", "microsoft word", "document"],
                "excel": ["excel", "spreadsheet"],
                "powerpoint": ["powerpoint", "presentation"],
            }

    def _calibrate_microphone(self) -> None:
        logger.info("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        logger.info("Microphone calibrated!")

    def get_command(self) -> str | None:
        if self.config.use_voice:
            return self._listen_for_command()
        return self._get_text_command()

    def _get_text_command(self) -> str | None:
        try:
            command = input("\nEnter your command: ").strip()
            if command:
                logger.info("You typed: %s", command)
                return command.lower()
            return None
        except (EOFError, KeyboardInterrupt):
            return None

    def _listen_for_command(self) -> str | None:
        try:
            with self.microphone as source:
                logger.info("Listening for command (Hindi/English)...")
                audio = self.recognizer.listen(source, timeout=20, phrase_time_limit=10)

            logger.info("Processing speech...")

            # Try Hindi first, fall back to English
            command = None
            detected_lang = "en"
            try:
                command = self.recognizer.recognize_google(audio, language="hi-IN")
                detected_lang = "hi"
                logger.info("Detected Hindi: %s", command)
            except Exception:
                pass

            if not command:
                try:
                    command = self.recognizer.recognize_google(audio, language="en-US")
                    detected_lang = "en"
                    logger.info("Detected English: %s", command)
                except Exception:
                    logger.warning("Could not understand the audio in Hindi or English")
                    return None

            # Translate Hindi to English
            if detected_lang == "hi":
                try:
                    from deep_translator import GoogleTranslator
                    translated = GoogleTranslator(source="hi", target="en").translate(command)
                    logger.info("Translated to English: %s", translated)
                    print(f"🎤 Hindi: {command}")
                    print(f"🔄 English: {translated}")
                    command = translated
                except Exception as e:
                    logger.warning("Translation failed, using original: %s", e)
                    print(f"🎤 You said: {command}")
            else:
                print(f"🎤 You said: {command}")

            return command.lower()

        except Exception as e:
            logger.error("Error in voice recognition: %s", e)
            return None

    def take_screenshot(self) -> Image.Image:
        return pyautogui.screenshot()

    def find_element_with_ai(
        self, screenshot: Image.Image, target_description: str
    ) -> tuple[int, int] | None:
        return self.llm.find_element(screenshot, target_description)

    def interpret_command_with_ai(self, command: str) -> dict[str, Any]:
        return self.llm.interpret_command(command, self.is_mac)

    def execute_action(self, action_data: dict[str, Any]) -> bool:
        try:
            steps = action_data.get("steps", [])
            if not steps:
                logger.warning("No steps to execute")
                return False

            success_count = 0
            for i, step in enumerate(steps):
                desc = step.get("description", "Executing step")
                logger.info("Step %d/%d: %s", i + 1, len(steps), desc)

                if self._execute_single_step(step):
                    success_count += 1
                    logger.info("Step %d completed", i + 1)
                else:
                    logger.warning("Step %d failed", i + 1)

                wait_time = step.get("wait_seconds", 0.5)
                time.sleep(wait_time)

            logger.info("Completed %d/%d steps", success_count, len(steps))
            return success_count > 0

        except Exception as e:
            logger.error("Error executing action: %s", e)
            return False

    def _execute_single_step(self, step: dict[str, Any]) -> bool:
        try:
            action = step.get("action", "").lower()

            if action == "click":
                return self._handle_click_action(step)
            if action == "type":
                return self._handle_type_action(step)
            if action == "scroll":
                return self._handle_scroll_action(step)
            if action == "open":
                return self._handle_open_action(step)
            if action == "navigate":
                url = step.get("url", step.get("target", ""))
                return self._navigate_to_url(url) if url else False
            if action == "close":
                return self._handle_close_action(step)
            if action == "hotkey":
                return self._handle_hotkey_action(step)
            if action == "wait":
                return self._handle_wait_action(step)
            if action == "minimize":
                return self._handle_minimize_action(step)
            if action == "maximize":
                return self._handle_maximize_action(step)

            logger.warning("Unknown action: %s", action)
            return False

        except Exception as e:
            logger.error("Error executing step: %s", e)
            return False

    def _handle_click_action(self, action_data: dict[str, Any]) -> bool:
        try:
            target = action_data.get("target", "")
            screenshot = self.take_screenshot()
            coordinates = self.find_element_with_ai(screenshot, target)

            if coordinates and len(coordinates) == 2:
                x, y = int(coordinates[0]), int(coordinates[1])
                logger.info("Clicking at (%d, %d)", x, y)
                pyautogui.click(x, y)
                return True

            logger.warning("AI could not find target: %s", target)
            if "search" in target.lower():
                return self._fallback_search_strategies(target)
            return False

        except Exception as e:
            logger.error("Error in click action: %s", e)
            return False

    def _fallback_search_strategies(self, target: str) -> bool:
        logger.info("Trying fallback strategies for search...")
        try:
            if "youtube" in target.lower() or "search" in target.lower():
                logger.info("Trying keyboard shortcut: /")
                pyautogui.press("/")
                time.sleep(0.5)
                return True

            logger.info("Trying Ctrl+F / Cmd+F")
            if self.is_mac:
                pyautogui.hotkey("cmd", "f")
            else:
                pyautogui.hotkey("ctrl", "f")
            time.sleep(0.5)
            pyautogui.press("escape")

            logger.info("Trying Tab navigation")
            for _ in range(5):
                pyautogui.press("tab")
                time.sleep(0.2)

            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            top_y = screen_height // 6
            logger.info("Trying general search area at (%d, %d)", center_x, top_y)
            pyautogui.click(center_x, top_y)
            time.sleep(0.5)

            return True

        except Exception as e:
            logger.error("Fallback strategies failed: %s", e)
            return False

    def _handle_type_action(self, action_data: dict[str, Any]) -> bool:
        text = action_data.get("text_to_type", "")
        if text:
            logger.info("Typing: %s", text)
            pyautogui.write(text)
            return True
        return False

    def _handle_scroll_action(self, action_data: dict[str, Any]) -> bool:
        direction = action_data.get("direction", "down")
        scroll_amount = 3

        if direction in ("up",):
            pyautogui.scroll(scroll_amount)
        elif direction in ("down",):
            pyautogui.scroll(-scroll_amount)

        logger.info("Scrolled %s", direction)
        return True

    def _handle_open_action(self, action_data: dict[str, Any]) -> bool:
        try:
            app_name = action_data.get("application", "").lower()
            url = action_data.get("url", "")

            # If a URL is provided, open it directly in the browser
            if url:
                return self._open_url(url)

            if self._try_direct_launch(app_name):
                return True

            target = action_data.get("target", f"{app_name} icon")
            screenshot = self.take_screenshot()
            coordinates = self.find_element_with_ai(screenshot, target)

            if coordinates and len(coordinates) == 2:
                x, y = int(coordinates[0]), int(coordinates[1])
                logger.info("Clicking %s at (%d, %d)", app_name, x, y)
                pyautogui.doubleClick(x, y)
                return True

            logger.warning("Could not find %s", app_name)
            return False

        except Exception as e:
            logger.error("Error in open action: %s", e)
            return False

    def _open_url(self, url: str) -> bool:
        """Open a URL — reuse existing browser window if open, else launch new."""
        try:
            logger.info("Opening URL: %s", url)
            if self.is_windows:
                if self._is_browser_running():
                    # Browser already open — focus it then navigate via address bar
                    self._focus_any_browser()
                    time.sleep(0.5)
                    return self._navigate_to_url(url)
                else:
                    # No browser open — launch Chrome/Edge then navigate
                    launched = False
                    for exe in ("chrome.exe", "msedge.exe", "firefox.exe"):
                        if self._run_windows_command(exe):
                            launched = True
                            time.sleep(2)
                            self._focus_any_browser()
                            time.sleep(0.5)
                            return self._navigate_to_url(url)
                    if not launched:
                        import webbrowser
                        webbrowser.open(url)
            else:
                import webbrowser
                webbrowser.open(url)
            return True
        except Exception as e:
            logger.error("Failed to open URL %s: %s", url, e)
            return False

    def _focus_any_browser(self) -> bool:
        """Bring the first visible browser window to the foreground. Returns True if found."""
        if not self.is_windows:
            return False
        try:
            import ctypes
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            browser_titles = ["chrome", "firefox", "edge", "mozilla"]
            found_hwnd: list[int] = []

            @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)  # type: ignore
            def callback(hwnd: int, _: int) -> bool:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.lower()
                        if any(b in title for b in browser_titles):
                            found_hwnd.append(hwnd)
                return True

            user32.EnumWindows(callback, 0)
            if found_hwnd:
                hwnd = found_hwnd[0]
                # Restore if minimised
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.1)
                # Force foreground using thread attachment trick
                foreground_hwnd = user32.GetForegroundWindow()
                foreground_tid = user32.GetWindowThreadProcessId(foreground_hwnd, None)
                target_tid = user32.GetWindowThreadProcessId(hwnd, None)
                if foreground_tid != target_tid:
                    user32.AttachThreadInput(foreground_tid, target_tid, True)
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                    user32.AttachThreadInput(foreground_tid, target_tid, False)
                else:
                    user32.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                logger.info("Focused browser window (hwnd=%d)", hwnd)
                return True
        except Exception as e:
            logger.warning("Could not focus browser: %s", e)
        return False

    def _is_browser_running(self) -> bool:
        """Check if any browser window is currently open on Windows."""
        try:
            import ctypes
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            browser_titles = ["chrome", "firefox", "edge", "mozilla"]
            found = []

            @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)  # type: ignore
            def callback(hwnd: int, _: int) -> bool:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.lower()
                        if any(b in title for b in browser_titles):
                            found.append(hwnd)
                return True

            user32.EnumWindows(callback, 0)
            return len(found) > 0
        except Exception:
            return False

    def _navigate_to_url(self, url: str) -> bool:
        """Type a URL into the focused browser's address bar and navigate."""
        try:
            logger.info("Navigating to: %s", url)
            pyautogui.hotkey("ctrl", "l")  # focus address bar
            time.sleep(0.6)
            pyautogui.hotkey("ctrl", "a")  # select all existing text
            time.sleep(0.2)
            # Use pyperclip to paste URL instead of typewrite (faster, handles special chars)
            try:
                import pyperclip
                pyperclip.copy(url)
                pyautogui.hotkey("ctrl", "v")
            except Exception:
                pyautogui.typewrite(url, interval=0.03)
            time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(1.5)
            return True
        except Exception as e:
            logger.error("Navigation failed: %s", e)
            return False

    def _try_direct_launch(self, app_name: str) -> bool:
        try:
            if self.is_mac:
                return self._launch_mac_app(app_name)
            return self._launch_windows_app(app_name)
        except Exception as e:
            logger.error("Direct launch failed: %s", e)
            return False

    def _launch_mac_app(self, app_name: str) -> bool:
        try:
            app_mapping = {
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "safari": "Safari",
                "textedit": "TextEdit",
                "text edit": "TextEdit",
                "calculator": "Calculator",
                "finder": "Finder",
                "terminal": "Terminal",
                "preferences": "System Preferences",
                "settings": "System Preferences",
            }

            app_to_launch = app_mapping.get(app_name.lower(), app_name.title())

            if "spotlight" in app_name.lower():
                pyautogui.hotkey("cmd", "space")
                return True

            logger.info("Attempting to launch: %s", app_to_launch)
            try:
                result = subprocess.run(
                    ["open", "-a", app_to_launch],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0:
                    logger.info("Successfully launched %s", app_to_launch)
                    return True

                logger.warning("Failed to launch %s: %s", app_to_launch, result.stderr)
                if app_to_launch != app_name:
                    result = subprocess.run(
                        ["open", "-a", app_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        logger.info("Successfully launched %s", app_name)
                        return True
                return False

            except subprocess.TimeoutExpired:
                logger.warning("Timeout launching %s, but it may have started", app_to_launch)
                return True

        except Exception as e:
            logger.error("Mac app launch failed: %s", e)
            return False

    def _focus_foreground(self, app_name: str, wait: float = 1.5) -> None:
        """Wait for a Windows app to appear then force it to the foreground."""
        if not self.is_windows:
            return
        time.sleep(wait)
        try:
            import ctypes
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]

            # Try to find the window by a partial title match
            needle = app_name.strip().lower()

            # Map common app names to expected window title fragments
            title_hints = {
                "calculator": "calculator",
                "calc": "calculator",
                "notepad": "notepad",
                "chrome": "chrome",
                "google chrome": "chrome",
                "firefox": "firefox",
                "edge": "edge",
                "microsoft edge": "edge",
                "explorer": "file explorer",
                "file explorer": "file explorer",
                "files": "file explorer",
                "word": "word",
                "excel": "excel",
                "powerpoint": "powerpoint",
                "paint": "paint",
                "cmd": "command prompt",
                "command prompt": "command prompt",
                "terminal": "terminal",
                "powershell": "powershell",
            }
            search = title_hints.get(needle, needle)

            found_hwnd: list[int] = []

            @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)  # type: ignore
            def enum_callback(hwnd: int, _lparam: int) -> bool:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.lower()
                        if search in title:
                            found_hwnd.append(hwnd)
                return True

            user32.EnumWindows(enum_callback, 0)

            if found_hwnd:
                hwnd = found_hwnd[0]
                # Restore if minimised
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
                logger.info("Brought '%s' window to foreground", app_name)
            else:
                logger.warning("Could not find window for '%s' to focus", app_name)
        except Exception as e:
            logger.warning("Window focus failed for '%s': %s", app_name, e)

    def _launch_windows_app(self, app_name: str) -> bool:
        name = app_name.strip().lower()
        if not name:
            return False

        # Direct map lookup
        command = self.WINDOWS_APP_COMMANDS.get(name)
        if command and self._run_windows_command(command):
            self._focus_foreground(app_name)
            return True

        # Start Menu shortcut search
        shortcut = self._find_start_menu_shortcut(app_name)
        if shortcut:
            try:
                os.startfile(shortcut)  # type: ignore[attr-defined]
                logger.info("Launched %s via Start Menu shortcut", shortcut)
                self._focus_foreground(app_name)
                return True
            except OSError as e:
                logger.warning("Failed to launch shortcut %s: %s", shortcut, e)

        # If it sounds like a browser, try every known browser exe
        browser_keywords = {"browser", "web", "internet", "chrome", "edge", "firefox", "safari"}
        if any(kw in name for kw in browser_keywords):
            for fallback in ("chrome.exe", "msedge.exe", "firefox.exe"):
                if self._run_windows_command(fallback):
                    self._focus_foreground(fallback.replace(".exe", ""))
                    return True

        # Use 'start' shell command only for names that look like real executables
        # (contain .exe, or are single words without spaces — avoids the Windows
        # "cannot find 'web browser'" error dialog on multi-word phrases)
        safe_to_shell = "." in app_name or " " not in app_name.strip()
        if safe_to_shell:
            try:
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                self._focus_foreground(app_name)
                return True
            except OSError as e:
                logger.error("Windows app launch failed for %s: %s", app_name, e)

        logger.warning("Could not launch '%s' — no matching app found", app_name)
        return False

    def _run_windows_command(self, command: str) -> bool:
        try:
            if command.endswith(":"):  # URI scheme, e.g. ms-settings:
                os.startfile(command)  # type: ignore[attr-defined]
                return True
            subprocess.Popen([command])
            return True
        except OSError:
            pass

        # Try known full install paths
        for candidate in self.WINDOWS_APP_PATHS.get(command, []):
            resolved = os.path.expandvars(candidate)
            if os.path.exists(resolved):
                try:
                    subprocess.Popen([resolved])
                    return True
                except OSError as e:
                    logger.warning("Failed to launch %s: %s", resolved, e)

        return False

    def _find_start_menu_shortcut(self, app_name: str) -> str | None:
        needle = app_name.strip().lower()
        search_dirs = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        ]
        for base in search_dirs:
            if not base.exists():
                continue
            for shortcut in base.rglob("*.lnk"):
                if needle in shortcut.stem.lower():
                    return str(shortcut)
        return None

    def _handle_close_action(self, action_data: dict[str, Any]) -> bool:
        try:
            if self.is_mac:
                pyautogui.hotkey("cmd", "q")
                logger.info("Sent quit command (Cmd+Q)")
            else:
                pyautogui.hotkey("alt", "f4")
                logger.info("Sent close command (Alt+F4)")
            return True
        except Exception as e:
            logger.error("Error closing application: %s", e)
            return False

    def _handle_hotkey_action(self, action_data: dict[str, Any]) -> bool:
        hotkey = action_data.get("hotkey", [])
        if hotkey and isinstance(hotkey, list):
            logger.info("Pressing hotkey: %s", " + ".join(hotkey))
            pyautogui.hotkey(*hotkey)
            return True
        return False

    def _handle_wait_action(self, action_data: dict[str, Any]) -> bool:
        wait_time = action_data.get("wait_seconds", 1)
        logger.info("Waiting %d seconds...", wait_time)
        time.sleep(wait_time)
        return True

    def _handle_minimize_action(self, action_data: dict[str, Any]) -> bool:
        if self.is_mac:
            pyautogui.hotkey("cmd", "m")
        else:
            pyautogui.hotkey("win", "down")
        logger.info("Minimized window")
        return True

    def _handle_maximize_action(self, action_data: dict[str, Any]) -> bool:
        if self.is_mac:
            screenshot = self.take_screenshot()
            coordinates = self.find_element_with_ai(
                screenshot, "green maximize button in title bar"
            )
            if coordinates:
                pyautogui.click(coordinates[0], coordinates[1])
            else:
                pyautogui.hotkey("cmd", "ctrl", "f")
        else:
            pyautogui.hotkey("win", "up")
        logger.info("Maximized window")
        return True

    def run(self) -> None:
        mode = "Voice" if self.config.use_voice else "Text"
        input_icon = "🎤" if self.config.use_voice else "💬"

        print(f"\n=== {mode} Computer Controller Started ===")
        print(f"{input_icon} Dynamic AI-Powered {mode} Control")
        print("Say/Type anything you want to do with your computer!")
        print("\nExamples:")
        print("• 'open bin' → Opens any app/folder named bin")
        print("• 'go on chrome and open a new tab' → Opens Chrome then new tab")
        print("• 'search for cats on google' → Opens browser, searches cats")
        print("• 'make the text bigger' → Uses zoom hotkeys")
        print("• 'close this and open calculator' → Closes window, opens calc")
        print("• 'take a screenshot' → Takes screenshot")
        print("• 'scroll down and click the blue button' → Scrolls then finds button")

        exit_hint = "Say" if self.config.use_voice else "Type"
        print(f"{exit_hint} 'exit' or 'quit' to stop.\n")

        while True:
            try:
                command = self.get_command()
                if command is None:
                    continue

                if any(word in command for word in ["exit", "quit", "stop", "goodbye"]):
                    print("Goodbye!")
                    break

                action_data = self.interpret_command_with_ai(command)

                if action_data.get("confidence", 0) < 0.3:
                    print(f"Command not understood clearly. Reasoning: {action_data.get('reasoning', 'unknown')}. Please try again.")
                    continue

                success = self.execute_action(action_data)

                if success:
                    print("Command executed successfully!")
                else:
                    print("Failed to execute command")

                time.sleep(1)

            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                break
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                continue
