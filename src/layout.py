"""Define bookshelf layout data.

Provides fixed day-slot layouts for 28-, 29-, 30-, and 31-day months.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .path_utils import resource_path
from .ui_constants import CANVAS_HEIGHT, CANVAS_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH


# Shared geometry types used by shelf click and drawing logic.
CellRect = tuple[int, int, int, int]
Size = tuple[int, int]


SHELF_WIDTH = 490
SHELF_HEIGHT = 650
CANVAS_X = 16
CANVAS_Y = 188
SHELF_X = ((WINDOW_WIDTH - SHELF_WIDTH) // 2) - CANVAS_X
SHELF_Y = ((WINDOW_HEIGHT - SHELF_HEIGHT) // 2) - CANVAS_Y
DEFAULT_BOOK_SIZE = (30, 82)


def rect_from_xywh(left: int, top: int, width: int, height: int) -> CellRect:
    """Build a click rectangle from top-left coordinates plus width and height."""
    return (left, top, left + width, top + height)


@dataclass(slots=True)
class BookSlotSpec:
    """Manual slot specification relative to the top-left corner of the shelf image."""

    day: int | None
    book_left: int
    book_top: int
    book_width: int
    book_height: int
    click_left: int
    click_top: int
    click_width: int
    click_height: int
    image_name: str | None = None


def slot_at(
    book_left: int,
    book_top: int,
    book_width: int,
    book_height: int,
    *,
    day: int | None = None,
    click_left: int | None = None,
    click_top: int | None = None,
    click_width: int | None = None,
    click_height: int | None = None,
    image_name: str | None = None,
) -> BookSlotSpec:
    """Create a manual slot using shelf-local coordinates."""
    return BookSlotSpec(
        day=day,
        book_left=book_left,
        book_top=book_top,
        book_width=book_width,
        book_height=book_height,
        click_left=book_left if click_left is None else click_left,
        click_top=book_top if click_top is None else click_top,
        click_width=book_width if click_width is None else click_width,
        click_height=book_height if click_height is None else click_height,
        image_name=image_name,
    )


def slot_for(
    day: int,
    book_left: int,
    book_top: int,
    book_width: int,
    book_height: int,
    *,
    click_left: int | None = None,
    click_top: int | None = None,
    click_width: int | None = None,
    click_height: int | None = None,
    image_name: str | None = None,
) -> BookSlotSpec:
    """Create a manual slot explicitly bound to a calendar day."""
    return slot_at(
        book_left,
        book_top,
        book_width,
        book_height,
        day=day,
        click_left=click_left,
        click_top=click_top,
        click_width=click_width,
        click_height=click_height,
        image_name=image_name,
    )


@dataclass(slots=True)
class BookSlot:
    """Stores the manual click area and draw coordinates for one day."""

    day: int
    click_rect: CellRect
    book_position: Point
    book_size: Size
    image_name: str | None = None


@dataclass(slots=True)
class MonthLayoutConfig:
    """Stores one manually configured bookshelf scene for a month length."""

    days_count: int
    shelf_image_path: Path
    window_background_path: Path
    canvas_width: int
    canvas_height: int
    canvas_x: int
    canvas_y: int
    shelf_x: int
    shelf_y: int
    shelf_width: int
    shelf_height: int
    slots: dict[int, BookSlot]

    def get_cell_rect(self, day: int) -> CellRect:
        return self.slots[day].click_rect

    def get_book_position(self, day: int) -> Point:
        return self.slots[day].book_position

    def get_book_size(self, day: int) -> Size:
        return self.slots[day].book_size

    def get_book_image_name(self, day: int) -> str | None:
        return self.slots[day].image_name

    def contains_point(self, day: int, x: int, y: int) -> bool:
        x1, y1, x2, y2 = self.get_cell_rect(day)
        return x1 <= x <= x2 and y1 <= y <= y2


class LayoutManager:
    """Build and return month-specific bookshelf layouts."""

    def __init__(self, assets_root: Path | str | None = None) -> None:
        self._assets_root = Path(assets_root) if assets_root is not None else resource_path("assets")
        self._canvas_x = CANVAS_X
        self._canvas_y = CANVAS_Y
        self._canvas_width = CANVAS_WIDTH
        self._canvas_height = CANVAS_HEIGHT
        shelves_root = self._assets_root / "shelves"
        positions_31 = _positions_31()
        self._layouts = {
            28: self._build_layout(28, shelves_root / "shelf_28.png", _positions_28(positions_31)),
            29: self._build_layout(29, shelves_root / "shelf_29.png", _positions_29(positions_31)),
            30: self._build_layout(30, shelves_root / "shelf_30.png", _positions_30(positions_31)),
            31: self._build_layout(31, shelves_root / "shelf_31.png", positions_31),
        }

    def get_layout(self, days_count: int) -> MonthLayoutConfig:
        return self.get_layout_for_month(days_count, 1)

    def get_layout_for_month(self, days_count: int, month: int) -> MonthLayoutConfig:
        try:
            base_layout = self._layouts[days_count]
        except KeyError as error:
            raise ValueError(f"No bookshelf layout is configured for {days_count} days.") from error
        return self._scale_layout(base_layout, self._background_path_for_month(month))

    def configure_viewport(self, canvas_x: int, canvas_y: int, canvas_width: int, canvas_height: int) -> None:
        self._canvas_x = canvas_x
        self._canvas_y = canvas_y
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height

    def _build_layout(
        self,
        days_count: int,
        shelf_image_path: Path,
        positions: list[BookSlotSpec],
    ) -> MonthLayoutConfig:
        """Validate manual slot data and create a layout configuration."""
        if len(positions) != days_count:
            raise ValueError(f"Layout for {days_count} days must define exactly {days_count} positions.")

        slots: dict[int, BookSlot] = {}

        for item in positions:
            if item.day is None:
                raise ValueError("Manual slot definitions must be bound to explicit calendar days.")

            target_day = item.day
            local_book_left = item.book_left
            local_book_top = item.book_top
            book_size = (item.book_width, item.book_height)
            click_rect = rect_from_xywh(
                item.click_left,
                item.click_top,
                item.click_width,
                item.click_height,
            )
            image_name = item.image_name

            if target_day in slots:
                raise ValueError(f"Duplicate slot definition for day {target_day}.")

            slots[target_day] = BookSlot(
                day=target_day,
                click_rect=click_rect,
                book_position=(local_book_left, local_book_top),
                book_size=book_size,
                image_name=image_name,
            )

        expected_days = set(range(1, days_count + 1))
        actual_days = set(slots.keys())
        if actual_days != expected_days:
            missing_days = sorted(expected_days - actual_days)
            raise ValueError(f"Layout for {days_count} days is missing slots for days: {missing_days}")

        return MonthLayoutConfig(
            days_count=days_count,
            shelf_image_path=shelf_image_path,
            window_background_path=self._background_path_for_month(1),
            canvas_width=CANVAS_WIDTH,
            canvas_height=CANVAS_HEIGHT,
            canvas_x=CANVAS_X,
            canvas_y=CANVAS_Y,
            shelf_x=SHELF_X,
            shelf_y=SHELF_Y,
            shelf_width=SHELF_WIDTH,
            shelf_height=SHELF_HEIGHT,
            slots=slots,
        )

    def _background_path_for_month(self, month: int) -> Path:
        backgrounds_root = self._assets_root / "backgrounds"
        return backgrounds_root / f"month_{month:02d}.png"

    def _scale_layout(self, base_layout: MonthLayoutConfig, background_path: Path) -> MonthLayoutConfig:
        """Shift shelf slot positions to match the current canvas viewport."""
        shifted_slots: dict[int, BookSlot] = {}
        for day, slot in base_layout.slots.items():
            shifted_slots[day] = BookSlot(
                day=slot.day,
                click_rect=(
                    slot.click_rect[0] + max(0, (self._canvas_width - base_layout.shelf_width) // 2),
                    slot.click_rect[1] + max(0, (self._canvas_height - base_layout.shelf_height) // 2),
                    slot.click_rect[2] + max(0, (self._canvas_width - base_layout.shelf_width) // 2),
                    slot.click_rect[3] + max(0, (self._canvas_height - base_layout.shelf_height) // 2),
                ),
                book_position=(
                    slot.book_position[0] + max(0, (self._canvas_width - base_layout.shelf_width) // 2),
                    slot.book_position[1] + max(0, (self._canvas_height - base_layout.shelf_height) // 2),
                ),
                book_size=slot.book_size,
                image_name=slot.image_name,
            )

        return MonthLayoutConfig(
            days_count=base_layout.days_count,
            shelf_image_path=base_layout.shelf_image_path,
            window_background_path=background_path,
            canvas_width=self._canvas_width,
            canvas_height=self._canvas_height,
            canvas_x=self._canvas_x,
            canvas_y=self._canvas_y,
            shelf_x=max(0, (self._canvas_width - base_layout.shelf_width) // 2),
            shelf_y=max(0, (self._canvas_height - base_layout.shelf_height) // 2),
            shelf_width=base_layout.shelf_width,
            shelf_height=base_layout.shelf_height,
            slots=shifted_slots,
        )


def _trim_positions(positions_31: list[BookSlotSpec], days_count: int) -> list[BookSlotSpec]:
    """Reuse the 31-day shelf coordinates while dropping the last calendar days."""
    return [slot for slot in positions_31 if slot.day is not None and slot.day <= days_count]


def _positions_28(positions_31: list[BookSlotSpec]) -> list[BookSlotSpec]:
    return _trim_positions(positions_31, 28)


def _positions_29(positions_31: list[BookSlotSpec]) -> list[BookSlotSpec]:
    return _trim_positions(positions_31, 29)


def _positions_30(positions_31: list[BookSlotSpec]) -> list[BookSlotSpec]:
    return _trim_positions(positions_31, 30)


def _positions_31() -> list[BookSlotSpec]:
    return [
        slot_for(1, 26, 62, 57, 141, image_name="1.png"),
        slot_for(2, 74, 49, 50, 153, image_name="2.png"),
        slot_for(3, 115, 54, 50, 148, image_name="3.png"),
        slot_for(4, 158, 64, 43, 137, image_name="4.png"),
        slot_for(5, 197, 66, 43, 134, image_name="5.png"),
        slot_for(6, 238, 88, 37, 113, image_name="6.png"),
        slot_for(7, 270, 53, 47, 148, image_name="7.png"),
        slot_for(8, 311, 61, 40, 140, image_name="8.png"),
        slot_for(9, 350, 48, 51, 153, image_name="9.png"),
        slot_for(10, 398, 61, 40, 140, image_name="10.png"),
        slot_for(11, 17, 280, 53, 141, image_name="11.png"),
        slot_for(12, 66, 276, 38, 143, image_name="12.png"),
        slot_for(13, 99, 260, 47, 160, image_name="13.png"),
        slot_for(14, 138, 268, 50, 153, image_name="14.png"),
        slot_for(15, 181, 270, 47, 145, image_name="15.png"),
        slot_for(16, 223, 260, 47, 160, image_name="16.png"),
        slot_for(17, 265, 268, 54, 148, image_name="17.png"),
        slot_for(18, 311, 264, 51, 150, image_name="18.png"),
        slot_for(19, 360, 263, 51, 152, image_name="19.png"),
        slot_for(20, 411, 285, 48, 139, image_name="20.png"),
        slot_for(31, 403, 460, 61, 155, image_name="31.png"),
        slot_for(30, 358, 453, 66, 157, image_name="30.png"),
        slot_for(29, 331, 458, 62, 155, image_name="29.png"),
        slot_for(28, 298, 471, 51, 138, image_name="28.png"),
        slot_for(27, 257, 455, 65, 156, image_name="27.png"),
        slot_for(26, 237, 484, 36, 129, image_name="26.png"),
        slot_for(25, 191, 464, 51, 151, image_name="25.png"),
        slot_for(24, 151, 458, 51, 149, image_name="24.png"),
        slot_for(23, 99, 456, 64, 155, image_name="23.png"),
        slot_for(22, 65, 455, 61, 156, image_name="22.png"),
        slot_for(21, 26, 455, 61, 156, image_name="21.png"),
    ]
