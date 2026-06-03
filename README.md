# Cozy Library

Cozy Library is a one-habit desktop tracker built with Python and Tkinter. Each completed day appears as a book on a bookshelf-style calendar, combining a small daily habit workflow with a cozy visual desktop interface.

## Features

- track one habit at a time;
- edit the habit description without resetting completion history;
- mark or unmark today;
- toggle completion for visible days in the current or past months;
- browse previous and next months;
- view total completed days and selected-month completion stats;
- open a statistics window for chart-based month and year summaries;
- configure desktop reminders, startup behavior, and navigation hotkeys in Settings;
- import validated JSON from another file;
- export the current state to a JSON file;
- reset all data only after confirmation;
- continue working with fallback rendering when optional image/font features are unavailable.

## Run From Source

Requirements:

- Python 3.11 or newer
- Pillow
- plyer
- pystray

Install runtime dependencies:

```powershell
pip install -r requirements.txt
```

Run from the project folder:

```powershell
python main.py
```

## Build Note

`requirements.txt` contains runtime dependencies only: the packages needed to run Cozy Library from source.

PyInstaller is treated as build-only tooling and is intentionally documented separately in [BUILD.md](BUILD.md).

## Project Structure

```text
bookshelf_habit_tracker/
  main.py
  requirements.txt
  BUILD.md
  README.md
  CozyLibrary.spec
  data/
    habit_data.json
  assets/
  src/
    main_window.py         # app coordinator
    settings_dialog.py     # settings window and editors
    description_panel.py   # description display/edit panel
    header_view.py         # header canvas/background/text view
    footer_view.py         # footer canvas/background/text view
    shelf_view.py          # bookshelf calendar rendering
    statistics_window.py   # statistics charts and summaries
    models.py              # application state models
    storage.py             # JSON load/save/import/export/default recovery
    notification_service.py
    startup_service.py
    tray_service.py
    uninstall_service.py
    ui_rendering.py        # shared Pillow/Tk text rendering helpers
    background_utils.py    # shifted background viewport helpers
    layout.py
    sprites.py
    drawable.py
    date_service.py
    path_utils.py
    exceptions.py
    ui_constants.py
```

## Runtime Data

The repository includes a clean bundled `data/habit_data.json` file as package content.

On Windows, including PyInstaller builds, the live writable data file is stored at:

`%APPDATA%\CozyLibrary\habit_data.json`

Bundled `data/` files are treated as read-only resources, not as the active user save location.

If the runtime data file is missing, the application creates a default one automatically. If a data file is invalid or corrupted, the application falls back to a safe default state.

## Current Data Model Notes

The saved state includes:

- habit description text;
- created/opened timestamps;
- notification settings:
  - enabled flag
  - multiple reminder times
  - message template
- hotkey settings;
- startup preference;
- completion history keyed by ISO date strings.

## Architecture Notes

The current UI is split into a few focused pieces:

- `main_window.py` coordinates application lifecycle, layout math, persistence flow, and high-level refresh behavior;
- `settings_dialog.py` owns settings UI and draft-first settings save flow;
- `description_panel.py` owns the description area widgets and display/edit presentation state;
- `header_view.py` and `footer_view.py` own header/footer canvas rendering;
- `statistics_window.py` owns the charts and statistics display;
- `ui_rendering.py` and `background_utils.py` centralize shared rendering helpers.

## Import, Export, and Reset

- **Import JSON** validates the incoming file before replacing live state.
- **Export JSON** writes the current application state to a selected file.
- **Reset all data** clears the habit description, completion history, and related settings only after confirmation.

## Troubleshooting

- If reminders do not appear, make sure `plyer` is installed and notifications are enabled in Settings.
- If the tray icon is unavailable, make sure `pystray` and `Pillow` are installed.
- If text rendering falls back to plain canvas text, check that Pillow is installed and the bundled font assets are available.
- If build packaging is needed, follow [BUILD.md](BUILD.md) instead of installing build tools into `requirements.txt`.
- If runtime data seems missing, check `%APPDATA%\CozyLibrary\habit_data.json` rather than the bundled `data/` folder.
