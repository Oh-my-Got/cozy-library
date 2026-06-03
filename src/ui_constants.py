"""Store shared UI constants for Cozy Library.

Defines window geometry, colors, typography, and screen-fit helpers.
"""

from __future__ import annotations


MAIN_WINDOW_RATIO_WIDTH = 2
MAIN_WINDOW_RATIO_HEIGHT = 3
WINDOW_SCREEN_WIDTH_FRACTION = 0.96
WINDOW_SCREEN_HEIGHT_FRACTION = 1.0
WINDOW_TOP_CHROME_ALLOWANCE = 100
MIN_RESPONSIVE_WINDOW_WIDTH = 620
MIN_RESPONSIVE_WINDOW_HEIGHT = 775

WINDOW_WIDTH = 780
WINDOW_HEIGHT = 1080
WINDOW_MIN_WIDTH = 780
WINDOW_MIN_HEIGHT = 1080

WINDOW_BACKGROUND_FALLBACK = "#efe6d5"
CANVAS_BACKGROUND_FALLBACK = "#f7f3ea"
CANVAS_BORDER_COLOR = "#d1c7b8"
WINDOW_BACKGROUND_OFFSET_X = -78
WINDOW_BACKGROUND_OFFSET_Y = -125

LEFT_MARGIN = 16
RIGHT_MARGIN = 16
CONTENT_WIDTH = WINDOW_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

HEADER_MONTH_Y = 12
HEADER_DATE_Y = 40
HEADER_LABEL_X = 180
HEADER_LABEL_WIDTH = 420
HEADER_LABEL_HEIGHT = 28
HEADER_CANVAS_X = 180
HEADER_CANVAS_Y = 12
HEADER_CANVAS_WIDTH = 420
HEADER_CANVAS_HEIGHT = 56
HEADER_MONTH_FONT_SIZE = 24
HEADER_DATE_FONT_SIZE = 14
HEADER_TEXT_COLOR = "#2b2118"
UI_FONT_FAMILY = "Cascadia Mono"
UI_FONT_FALLBACK_FAMILY = "Consolas"
DESCRIPTION_DISPLAY_TEXT_COLOR = "#f7f5ef"
DESCRIPTION_EDIT_TEXT_COLOR = "#2b2118"
DESCRIPTION_EDIT_BACKGROUND_COLOR = "#f5eddc"

DESCRIPTION_ENTRY_X = 16
DESCRIPTION_ENTRY_Y = 70
DESCRIPTION_ENTRY_WIDTH = 748

TODAY_BUTTON_X = 16
TODAY_BUTTON_Y = 108

PREV_BUTTON_X = 16
NAVIGATION_Y = 12
NEXT_BUTTON_WIDTH = 114
PREV_BUTTON_WIDTH = 114
NEXT_BUTTON_X = WINDOW_WIDTH - RIGHT_MARGIN - NEXT_BUTTON_WIDTH

CANVAS_X = 16
CANVAS_Y = 180
CANVAS_WIDTH = 748
CANVAS_HEIGHT = 720

TOTAL_LABEL_X = 16
TOTAL_LABEL_Y = 916
MONTH_STATS_X = 16
MONTH_STATS_Y = 944
STATS_BUTTON_X = 16
STATS_BUTTON_Y = 976

STATS_WINDOW_WIDTH = 780
STATS_WINDOW_HEIGHT = 900
STATS_WINDOW_MIN_WIDTH = 780
STATS_WINDOW_MIN_HEIGHT = 900
STATS_HEADER_CANVAS_X = 180
STATS_HEADER_CANVAS_Y = 18
STATS_HEADER_CANVAS_WIDTH = 420
STATS_HEADER_CANVAS_HEIGHT = 56
STATS_HEADER_FONT_SIZE = 24
STATS_HEADER_TEXT = "DETAILED STATISTICS"
STATS_SECTION_TOP = 110
STATS_PIE_CANVAS_X = 24
STATS_PIE_CANVAS_Y = STATS_SECTION_TOP
STATS_PIE_CANVAS_SIZE = 300
STATS_TEXT_X = 360
STATS_TEXT_Y = STATS_SECTION_TOP
STATS_TEXT_WIDTH = 396
STATS_TEXT_LINE_GAP = 28
STATS_BAR_CANVAS_X = 24
STATS_BAR_CANVAS_Y = 440
STATS_BAR_CANVAS_WIDTH = 732
STATS_BAR_CANVAS_HEIGHT = 360
STATS_TEXT_COLOR = "#2b2118"
STATS_SUBTLE_TEXT_COLOR = "#5f5546"
STATS_COMPLETED_COLOR = "#5c8d55"
STATS_REMAINING_COLOR = "#c9c3b7"
STATS_AXIS_COLOR = "#8d8374"
STATS_WINDOW_BACKGROUND = "#f5eddc"
STATS_PANEL_BACKGROUND = "#efe4cf"
STATS_PANEL_BORDER = "#9f8e76"
STATS_SECTION_TITLE_FONT_SIZE = 20

SETTINGS_WINDOW_WIDTH = 780
SETTINGS_WINDOW_HEIGHT = 900
SETTINGS_WINDOW_MIN_WIDTH = 780
SETTINGS_WINDOW_MIN_HEIGHT = 900
SETTINGS_WINDOW_BACKGROUND = "#f5eddc"
SETTINGS_PANEL_BACKGROUND = "#efe4cf"
SETTINGS_PANEL_BORDER = "#9f8e76"
SETTINGS_HEADER_WIDTH = 420
SETTINGS_HEADER_HEIGHT = 56
SETTINGS_HEADER_X = 180
SETTINGS_HEADER_Y = 20
SETTINGS_HEADER_FONT_SIZE = 24
SETTINGS_PANEL_WIDTH = 732
SETTINGS_PANEL_X = 24
SETTINGS_NOTIFICATION_PANEL_Y = 104
SETTINGS_NOTIFICATION_PANEL_HEIGHT = 200
SETTINGS_HOTKEY_PANEL_Y = 322
SETTINGS_HOTKEY_PANEL_HEIGHT = 300
SETTINGS_BUTTON_ROW_Y = 812


def fit_window_to_screen(
    screen_width: int,
    screen_height: int,
    *,
    aspect_width: int,
    aspect_height: int,
    width_fraction: float = WINDOW_SCREEN_WIDTH_FRACTION,
    height_fraction: float = WINDOW_SCREEN_HEIGHT_FRACTION,
    chrome_allowance: int = WINDOW_TOP_CHROME_ALLOWANCE,
    min_width: int | None = None,
    min_height: int | None = None,
) -> tuple[int, int]:
    """Fit a window with a given aspect ratio into the available screen area."""
    available_width = max(320, int(screen_width * width_fraction))
    available_height = max(320, int((screen_height - chrome_allowance) * height_fraction))
    aspect_ratio = aspect_width / aspect_height

    height = available_height
    width = int(height * aspect_ratio)

    if width > available_width:
        width = available_width
        height = int(width / aspect_ratio)

    if min_width is not None:
        width = max(width, min(min_width, available_width))
        height = int(width / aspect_ratio)

    if min_height is not None and height < min(min_height, available_height):
        height = min(min_height, available_height)
        width = int(height * aspect_ratio)

    if width > available_width:
        width = available_width
        height = int(width / aspect_ratio)

    if height > available_height:
        height = available_height
        width = int(height * aspect_ratio)

    return max(320, width), max(320, height)
