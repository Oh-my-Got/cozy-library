# Windows Build Notes

These commands prepare and package the application with PyInstaller on Windows.

## Install Dependencies

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 -m pip install pyinstaller
```

`sqlite3` is part of the Python standard library, so no external database package or server is required.

## Syntax Check

```powershell
py -3.11 -m compileall .
```

## Build

```powershell
py -3.11 -m PyInstaller CozyLibrary.spec
```

## Notes

- Build output is written to `dist\`.
- Temporary PyInstaller files are written to `build\`.
- Runtime SQLite data is written to `%APPDATA%\CozyLibrary\cozy_library.db` on Windows.
- JSON remains available for import/export and migration from older `habit_data.json` data.
- Bundled `data\` files are read-only package resources, not the live save location.
- If `assets\app.ico` is missing, the application still runs and skips the window icon gracefully.
- `build\`, `dist\`, cache folders, and local database files should not be committed.
