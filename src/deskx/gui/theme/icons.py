"""SVG icon system.

A single coherent stroke-based icon family (Lucide geometry, 24x24
grid, 2px round-capped strokes) rendered to crisp ``QPixmap`` /
``QIcon`` at any size and tinted with any theme colour.

Usage::

    from deskx.gui.theme.icons import Icon, get_icon, icon_label

    button.setIcon(get_icon(Icon.UPLOAD, palette.primary, 16))
    layout.addWidget(icon_label(Icon.SHIELD, palette.success, 18))

Never use an emoji as a UI icon — add a glyph here instead.
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel


class Icon:
    """Names of every icon in the DeskX set."""

    # Navigation
    HOME: Final[str] = "home"
    FILES: Final[str] = "files"
    TRANSFORM: Final[str] = "transform"
    HISTORY: Final[str] = "history"
    REPORTS: Final[str] = "reports"
    SETTINGS: Final[str] = "settings"
    HELP: Final[str] = "help"
    PRIVACY: Final[str] = "privacy"

    # Workflow
    UPLOAD: Final[str] = "upload"
    PREVIEW: Final[str] = "preview"
    PIPELINE: Final[str] = "pipeline"
    PROCESS: Final[str] = "process"
    DOWNLOAD: Final[str] = "download"
    FOLDER: Final[str] = "folder"
    FOLDER_OPEN: Final[str] = "folder-open"
    FILE: Final[str] = "file"
    SPREADSHEET: Final[str] = "spreadsheet"
    TABLE: Final[str] = "table"
    COLUMNS: Final[str] = "columns"
    DATABASE: Final[str] = "database"

    # Status
    SUCCESS: Final[str] = "success"
    WARNING: Final[str] = "warning"
    ERROR: Final[str] = "error"
    INFO: Final[str] = "info"
    CHECK: Final[str] = "check"
    SHIELD: Final[str] = "shield"
    LOCK: Final[str] = "lock"

    # Actions
    SEARCH: Final[str] = "search"
    PLUS: Final[str] = "plus"
    CLOSE: Final[str] = "close"
    EDIT: Final[str] = "edit"
    TRASH: Final[str] = "trash"
    REFRESH: Final[str] = "refresh"
    EXTERNAL: Final[str] = "external"
    COPY: Final[str] = "copy"
    FILTER: Final[str] = "filter"

    # Direction
    ARROW_RIGHT: Final[str] = "arrow-right"
    ARROW_LEFT: Final[str] = "arrow-left"
    ARROW_DOWN: Final[str] = "arrow-down"
    CHEVRON_RIGHT: Final[str] = "chevron-right"
    CHEVRON_LEFT: Final[str] = "chevron-left"
    CHEVRON_DOWN: Final[str] = "chevron-down"

    # Transform categories
    CLEAN: Final[str] = "clean"
    MASK: Final[str] = "mask"
    REDACT: Final[str] = "redact"
    HASH: Final[str] = "hash"
    PSEUDONYM: Final[str] = "pseudonym"
    GENERALIZE: Final[str] = "generalize"
    TYPE: Final[str] = "type"
    CALENDAR: Final[str] = "calendar"

    # Theme / misc
    SUN: Final[str] = "sun"
    MOON: Final[str] = "moon"
    SPARKLE: Final[str] = "sparkle"
    CLOCK: Final[str] = "clock"
    DOT: Final[str] = "dot"


# Body of each SVG on a 24x24 grid.  ``fill`` glyphs are listed in
# _FILLED and are painted solid instead of stroked.
_PATHS: dict[str, str] = {
    Icon.HOME: (
        '<path d="m3 9.2 9-6.6 9 6.6V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<path d="M9.5 21v-7h5v7"/>'
    ),
    Icon.FILES: (
        '<path d="M14.5 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/>'
        '<path d="M14.5 2.5V7H19"/>'
        '<path d="M8.5 12.5h7"/><path d="M8.5 16.5h5"/>'
    ),
    Icon.TRANSFORM: (
        '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>'
        '<circle cx="9" cy="6" r="2.1"/><circle cx="15.5" cy="12" r="2.1"/>'
        '<circle cx="8" cy="18" r="2.1"/>'
    ),
    Icon.HISTORY: (
        '<path d="M3.2 12a8.8 8.8 0 1 0 2.7-6.3L3 8.4"/>'
        '<path d="M3 3.6V8.6h5"/><path d="M12 7.6V12l3 1.8"/>'
    ),
    Icon.REPORTS: (
        '<path d="M3.5 3v15.5a2 2 0 0 0 2 2H21"/>'
        '<rect x="7.5" y="11" width="3" height="6" rx="1"/>'
        '<rect x="13" y="6.5" width="3" height="10.5" rx="1"/>'
        '<rect x="18" y="13.5" width="2.6" height="3.5" rx="1"/>'
    ),
    Icon.SETTINGS: (
        '<circle cx="12" cy="12" r="2.9"/>'
        '<path d="M12 2.6h.9l.4 2.3a7.6 7.6 0 0 1 2 .84l1.93-1.34.64.63.63.64L17.2 7.6c.36.6.65 1.27.84 '
        '2l2.3.4v1.8l-2.3.4a7.6 7.6 0 0 1-.84 2l1.34 1.93-1.27 1.27-1.93-1.34a7.6 7.6 0 0 1-2 .84l-.4 '
        '2.3h-1.8l-.4-2.3a7.6 7.6 0 0 1-2-.84l-1.93 1.34-1.27-1.27L6.8 16.4a7.6 7.6 0 0 1-.84-2l-2.3-.4v-1.8l2.3-.4c.19-.73.48-1.4.84-2'
        'L5.46 7.87l1.27-1.27L8.66 7.94a7.6 7.6 0 0 1 2-.84l.4-2.3z"/>'
    ),
    Icon.HELP: (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M9.3 9.2a2.8 2.8 0 0 1 5.44.93c0 1.87-2.74 2.8-2.74 2.8"/>'
        '<path d="M12 17h.01"/>'
    ),
    Icon.PRIVACY: (
        '<path d="M12 21.5s7.5-3.6 7.5-9.4V5.4L12 2.5 4.5 5.4v6.7c0 5.8 7.5 9.4 7.5 9.4z"/>'
        '<path d="M9.2 11.9 11.3 14l3.5-3.6"/>'
    ),
    Icon.UPLOAD: (
        '<path d="M20.5 15.5V19a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-3.5"/>'
        '<path d="m7.8 8.3 4.2-4.2 4.2 4.2"/><path d="M12 4.1V15.6"/>'
    ),
    Icon.PREVIEW: (
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/>'
        '<circle cx="12" cy="12" r="2.9"/>'
    ),
    Icon.PIPELINE: (
        '<rect x="2.8" y="3" width="7" height="5.6" rx="1.8"/>'
        '<rect x="14.2" y="15.4" width="7" height="5.6" rx="1.8"/>'
        '<path d="M6.3 8.6v4.6a2 2 0 0 0 2 2h9.4"/>'
    ),
    Icon.PROCESS: (
        '<circle cx="12" cy="12" r="9"/><path d="M10.2 8.5 16 12l-5.8 3.5z"/>'
    ),
    Icon.DOWNLOAD: (
        '<path d="M20.5 15.5V19a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-3.5"/>'
        '<path d="m7.8 11.3 4.2 4.2 4.2-4.2"/><path d="M12 15.5V3.5"/>'
    ),
    Icon.FOLDER: (
        '<path d="M21 18.4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5.6a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.66.89l.79 '
        '1.18a2 2 0 0 0 1.66.89H19a2 2 0 0 1 2 2z"/>'
    ),
    Icon.FOLDER_OPEN: (
        '<path d="M3 8.2V5.6a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.66.89l.79 1.18a2 2 0 0 0 1.66.89H19a2 2 0 0 1 2 2v.64"/>'
        '<path d="M3.6 8.9h17.1a1.4 1.4 0 0 1 1.36 1.74l-1.9 8a1.9 1.9 0 0 1-1.85 1.46H4.6a1.9 1.9 0 0 1-1.9-1.9v-7.9a1.4 1.4 0 0 1 .9-1.4z"/>'
    ),
    Icon.FILE: (
        '<path d="M14.5 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/>'
        '<path d="M14.5 2.5V7H19"/>'
    ),
    Icon.SPREADSHEET: (
        '<path d="M14.5 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/>'
        '<path d="M14.5 2.5V7H19"/>'
        '<rect x="7.8" y="10.6" width="8.4" height="7.4" rx="1"/>'
        '<path d="M7.8 14.3h8.4"/><path d="M12 10.6V18"/>'
    ),
    Icon.TABLE: (
        '<rect x="3" y="4.2" width="18" height="15.6" rx="2.2"/>'
        '<path d="M3 9.6h18"/><path d="M9 9.6v10.2"/>'
    ),
    Icon.COLUMNS: (
        '<rect x="3" y="4.2" width="18" height="15.6" rx="2.2"/>'
        '<path d="M9 4.2v15.6"/><path d="M15 4.2v15.6"/>'
    ),
    Icon.DATABASE: (
        '<ellipse cx="12" cy="5.8" rx="8" ry="3.2"/>'
        '<path d="M4 5.8v12.4c0 1.77 3.58 3.2 8 3.2s8-1.43 8-3.2V5.8"/>'
        '<path d="M4 12c0 1.77 3.58 3.2 8 3.2s8-1.43 8-3.2"/>'
    ),
    Icon.SUCCESS: (
        '<circle cx="12" cy="12" r="9"/><path d="m8.2 12.2 2.6 2.6 5-5.2"/>'
    ),
    Icon.WARNING: (
        '<path d="M10.3 3.9 2.5 17.4A2 2 0 0 0 4.2 20.4h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'
        '<path d="M12 9.3v4"/><path d="M12 16.6h.01"/>'
    ),
    Icon.ERROR: (
        '<circle cx="12" cy="12" r="9"/><path d="m14.8 9.2-5.6 5.6"/><path d="m9.2 9.2 5.6 5.6"/>'
    ),
    Icon.INFO: (
        '<circle cx="12" cy="12" r="9"/><path d="M12 11.2v5"/><path d="M12 8h.01"/>'
    ),
    Icon.CHECK: '<path d="m4.8 12.4 4.6 4.6L19.2 7.2"/>',
    Icon.SHIELD: (
        '<path d="M12 21.5s7.5-3.6 7.5-9.4V5.4L12 2.5 4.5 5.4v6.7c0 5.8 7.5 9.4 7.5 9.4z"/>'
    ),
    Icon.LOCK: (
        '<rect x="4.2" y="10.2" width="15.6" height="10.6" rx="2.2"/>'
        '<path d="M8 10.2V7.4a4 4 0 0 1 8 0v2.8"/>'
    ),
    Icon.SEARCH: '<circle cx="11" cy="11" r="7"/><path d="m20.5 20.5-4.2-4.2"/>',
    Icon.PLUS: '<path d="M12 5.2v13.6"/><path d="M5.2 12h13.6"/>',
    Icon.CLOSE: '<path d="m18 6-12 12"/><path d="m6 6 12 12"/>',
    Icon.EDIT: (
        '<path d="M11.5 4.5H5a2 2 0 0 0-2 2V19a2 2 0 0 0 2 2h12.5a2 2 0 0 0 2-2v-6.5"/>'
        '<path d="M17.6 2.9a2.1 2.1 0 0 1 3 3L12 14.5l-4 1 1-4z"/>'
    ),
    Icon.TRASH: (
        '<path d="M3.8 6.2h16.4"/>'
        '<path d="M18.5 6.2V19a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2V6.2"/>'
        '<path d="M8.8 6.2V4.6a1.8 1.8 0 0 1 1.8-1.8h2.8a1.8 1.8 0 0 1 1.8 1.8v1.6"/>'
        '<path d="M10.3 10.8v5.6"/><path d="M13.7 10.8v5.6"/>'
    ),
    Icon.REFRESH: (
        '<path d="M20.5 11.5a8.5 8.5 0 1 1-2.4-5.6"/><path d="M20.8 3.6v5h-5"/>'
    ),
    Icon.EXTERNAL: (
        '<path d="M13.5 4.5H19.5V10.5"/><path d="M19.5 4.5 11 13"/>'
        '<path d="M18 14.4V18a2.5 2.5 0 0 1-2.5 2.5H6A2.5 2.5 0 0 1 3.5 18V8.5A2.5 2.5 0 0 1 6 6h3.6"/>'
    ),
    Icon.COPY: (
        '<rect x="8.6" y="8.6" width="12" height="12" rx="2.2"/>'
        '<path d="M15.4 5.6V5a2 2 0 0 0-2-2H5.4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2H6"/>'
    ),
    Icon.FILTER: '<path d="M21 4.2H3l7.2 8.2v6.1l3.6 1.8v-7.9z"/>',
    Icon.ARROW_RIGHT: '<path d="M4.5 12h14.4"/><path d="m13.2 6.2 5.7 5.8-5.7 5.8"/>',
    Icon.ARROW_LEFT: '<path d="M19.5 12H5.1"/><path d="m10.8 6.2-5.7 5.8 5.7 5.8"/>',
    Icon.ARROW_DOWN: '<path d="M12 4.5v14.4"/><path d="m6.2 13.2 5.8 5.7 5.8-5.7"/>',
    Icon.CHEVRON_RIGHT: '<path d="m9.2 5.5 6.6 6.5-6.6 6.5"/>',
    Icon.CHEVRON_LEFT: '<path d="m14.8 5.5-6.6 6.5 6.6 6.5"/>',
    Icon.CHEVRON_DOWN: '<path d="m5.5 9.2 6.5 6.6 6.5-6.6"/>',
    Icon.CLEAN: (
        '<path d="M12 2.8 13.7 8 19 9.7 13.7 11.4 12 16.6 10.3 11.4 5 9.7 10.3 8z"/>'
        '<path d="M18.4 15.2 19.3 17.8 21.9 18.7 19.3 19.6 18.4 22.2 17.5 19.6 14.9 18.7 17.5 17.8z"/>'
    ),
    Icon.MASK: (
        '<path d="M9.9 5.1A9.4 9.4 0 0 1 12 4.9c6 0 9.5 7.1 9.5 7.1a17.6 17.6 0 0 1-2.2 3.1"/>'
        '<path d="M6.4 6.8A17.4 17.4 0 0 0 2.5 12s3.5 7.1 9.5 7.1a9.2 9.2 0 0 0 4.1-.95"/>'
        '<path d="m3.2 3.2 17.6 17.6"/>'
    ),
    Icon.REDACT: (
        '<rect x="3" y="6.2" width="18" height="5.2" rx="1.4"/>'
        '<path d="M3 15.4h11"/><path d="M17.4 15.4H21"/><path d="M3 19.2h7"/>'
    ),
    Icon.HASH: (
        '<path d="M4.2 9.2h15.6"/><path d="M4.2 14.8h15.6"/>'
        '<path d="M10.4 3.5 8.6 20.5"/><path d="M15.4 3.5 13.6 20.5"/>'
    ),
    Icon.PSEUDONYM: (
        '<circle cx="12" cy="8.4" r="3.7"/>'
        '<path d="M5.2 20.4a6.8 6.8 0 0 1 13.6 0"/>'
    ),
    Icon.GENERALIZE: (
        '<path d="M3.4 16.6h4.2l2.6-9.2 3.4 12 2.4-6.4h4.6"/>'
    ),
    Icon.TYPE: (
        '<path d="M4.5 6.5v-2h15v2"/><path d="M12 4.5v15"/><path d="M8.6 19.5h6.8"/>'
    ),
    Icon.CALENDAR: (
        '<rect x="3.2" y="5" width="17.6" height="16" rx="2.4"/>'
        '<path d="M8 2.8v4.4"/><path d="M16 2.8v4.4"/><path d="M3.2 10.4h17.6"/>'
    ),
    Icon.SUN: (
        '<circle cx="12" cy="12" r="4.2"/>'
        '<path d="M12 2.6v2.2"/><path d="M12 19.2v2.2"/><path d="M4.4 4.4 6 6"/>'
        '<path d="M18 18 19.6 19.6"/><path d="M2.6 12h2.2"/><path d="M19.2 12h2.2"/>'
        '<path d="M4.4 19.6 6 18"/><path d="M18 6 19.6 4.4"/>'
    ),
    Icon.MOON: '<path d="M20.6 14.3A8.8 8.8 0 1 1 9.7 3.4a6.9 6.9 0 0 0 10.9 10.9z"/>',
    Icon.SPARKLE: (
        '<path d="M12 3 13.9 8.1 19 10 13.9 11.9 12 17 10.1 11.9 5 10l5.1-1.9z"/>'
    ),
    Icon.CLOCK: '<circle cx="12" cy="12" r="8.8"/><path d="M12 7.2V12l3.2 1.9"/>',
    Icon.DOT: '<circle cx="12" cy="12" r="4"/>',
}

# Icons drawn as solid shapes rather than strokes.
_FILLED: frozenset[str] = frozenset({Icon.DOT})

_SVG_TEMPLATE: Final[str] = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'width="{size}" height="{size}" fill="{fill}" stroke="{stroke}" '
    'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
    "{body}</svg>"
)

_pixmap_cache: dict[tuple[str, str, int, float, float], QPixmap] = {}


def svg_source(name: str, color: str, size: int = 18, stroke_width: float = 1.9) -> str:
    """Return the raw SVG markup for *name* tinted with *color*."""
    body = _PATHS.get(name)
    if body is None:
        body = _PATHS[Icon.DOT]
    filled = name in _FILLED
    return _SVG_TEMPLATE.format(
        size=size,
        body=body,
        fill=color if filled else "none",
        stroke="none" if filled else color,
        width=stroke_width,
    )


def get_pixmap(
    name: str,
    color: str,
    size: int = 18,
    stroke_width: float = 1.9,
    dpr: float = 2.0,
) -> QPixmap:
    """Render an icon to a device-pixel-ratio aware pixmap."""
    key = (name, color, size, stroke_width, dpr)
    cached = _pixmap_cache.get(key)
    if cached is not None:
        return cached

    renderer = QSvgRenderer(
        QByteArray(svg_source(name, color, size, stroke_width).encode("utf-8"))
    )
    pixmap = QPixmap(int(size * dpr), int(size * dpr))
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # The painter's logical area is the pixmap's *logical* size, so the
    # target rect is given in logical units; letting QSvgRenderer pick
    # the viewport instead would draw at device scale and clip.
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    _pixmap_cache[key] = pixmap
    return pixmap


def get_icon(
    name: str,
    color: str,
    size: int = 18,
    stroke_width: float = 1.9,
) -> QIcon:
    """Return a ``QIcon`` for *name* tinted with *color*."""
    return QIcon(get_pixmap(name, color, size, stroke_width))


def icon_label(
    name: str,
    color: str,
    size: int = 18,
    stroke_width: float = 1.9,
    parent=None,
) -> QLabel:
    """Return a transparent ``QLabel`` displaying an icon.

    The icon name is stored on the label so the theme engine can
    re-tint it when the palette changes.
    """
    label = QLabel(parent)
    label.setPixmap(get_pixmap(name, color, size, stroke_width))
    label.setFixedSize(size, size)
    label.setProperty("iconName", name)
    label.setProperty("iconSize", size)
    label.setProperty("iconStroke", stroke_width)
    label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    label.setStyleSheet("background: transparent; border: none;")
    return label


def retint_label(label: QLabel, color: str) -> None:
    """Re-render an :func:`icon_label` with a new colour."""
    name = label.property("iconName")
    if not name:
        return
    size = int(label.property("iconSize") or 18)
    stroke = float(label.property("iconStroke") or 1.9)
    label.setPixmap(get_pixmap(name, color, size, stroke))


def available_icons() -> list[str]:
    """Return every registered icon name (useful for tests)."""
    return sorted(_PATHS)


# ── QSS support ─────────────────────────────────────────────────────
#
# Qt Style Sheets can only reference images by file path (no data
# URIs), so glyphs used inside QSS rules — checkbox ticks, combo box
# arrows — are rendered once to PNGs in a cache directory.

_icon_file_cache: dict[tuple[str, str, int], str] = {}


def icon_file(name: str, color: str, size: int = 14) -> str:
    """Write an icon to a cached PNG and return a QSS-safe path."""
    key = (name, color, size)
    cached = _icon_file_cache.get(key)
    if cached is not None:
        return cached

    import hashlib
    import tempfile
    from pathlib import Path

    cache_dir = Path(tempfile.gettempdir()) / "deskx-icons"
    cache_dir.mkdir(parents=True, exist_ok=True)

    digest = hashlib.md5(f"{name}{color}{size}".encode()).hexdigest()[:12]
    target = cache_dir / f"{name}-{digest}.png"

    if not target.exists():
        pixmap = get_pixmap(name, color, size, dpr=2.0)
        pixmap.save(str(target), "PNG")

    path = str(target).replace("\\", "/")
    _icon_file_cache[key] = path
    return path
