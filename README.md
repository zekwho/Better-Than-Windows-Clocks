# Better Than Windows Clocks

A customizable, floating desktop clock application that displays multiple timezones simultaneously. As the name suggests, it offers functionality beyond the default Windows clock experience.

## Features

- Multiple timezone cards with large, clear time displays
- Cards can be resized, repositioned, and snapped together
- Modern dark theme UI with customizable elements
- Cards stay on desktop level - not always on top, but visible on the desktop
- Minimize to system tray with one click
- Auto-save of card positions and sizes
- Option to launch on Windows startup

## For Users

### Installation

#### Option 1: Executable (Recommended)
1. Download the latest `BetterThanWindowsClocks.exe` from the releases
2. No additional installation required - just run the executable
3. The application will request administrator permissions on startup

#### Option 2: From Source
1. Make sure you have Python 3.7+ installed on your system
2. Install the required dependencies:
   ```
   pip install customtkinter pillow pytz pystray
   ```
3. Run the application:
   ```
   python desktop_clocks.py
   ```

### Usage

1. The main window allows you to add timezone cards
2. Select a timezone from the dropdown and click "Add"
3. Cards can be:
   - Moved by dragging from any point on the card
   - Resized by dragging the bottom-right corner
   - Closed via the right-click menu
4. Cards will automatically snap together when dragged near each other
5. The main window can be minimized to the system tray
6. Access the app from the system tray by:
   - Left-clicking the icon to restore the main window
   - Right-clicking for options to show or exit

## For Developers

### Building the Executable

1. Ensure you have the required packages:
   ```
   pip install pyinstaller pystray pillow customtkinter pytz
   ```
2. Run the build script:
   ```
   python build_exe.py
   ```
3. The executable will be created in the `dist` folder

### Files

- `desktop_clocks.py` - Main application code
- `build_exe.py` - Script to build the executable
- `BTWC.ico` - Application icon file (optional)
- `clock_config.json` - Saved configuration (created automatically)

### Notes

- The executable is self-contained and includes all necessary dependencies
- Users do not need to install Python or any packages to run the executable
- UAC elevation is required for proper system tray functionality and startup settings 
