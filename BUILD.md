# Windows Build Notes

These commands prepare and package the application with PyInstaller on Windows.

## Install Dependencies

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 -m pip install pyinstaller
```

## Syntax Check

```powershell
py -3.11 -m compileall .
```

## Build: One Directory

```powershell
py -3.11 -m PyInstaller --noconfirm --clean --windowed --icon assets\app.ico --add-data "assets;assets" --add-data "data;data" --collect-submodules pystray --collect-submodules plyer --hidden-import pystray._base --hidden-import pystray._win32 --hidden-import plyer.platforms.win.notification --hidden-import plyer.platforms.win.libs.balloontip --hidden-import plyer.platforms.win.libs.win_api_defs --name CozyLibrary main.py
```

## Build: One File

```powershell
py -3.11 -m PyInstaller --noconfirm --clean --onefile --windowed --icon assets\app.ico --add-data "assets;assets" --add-data "data;data" --collect-submodules pystray --collect-submodules plyer --hidden-import pystray._base --hidden-import pystray._win32 --hidden-import plyer.platforms.win.notification --hidden-import plyer.platforms.win.libs.balloontip --hidden-import plyer.platforms.win.libs.win_api_defs --name CozyLibrary main.py
```

## Notes

- Runtime JSON data is written to `%APPDATA%\CozyLibrary\habit_data.json` on Windows.
- Bundled `data\` files are read-only package resources, not the live save location.
- If `assets\app.ico` is missing, the application still runs and skips the window icon gracefully.
