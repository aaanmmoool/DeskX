"""Generate the DeskX application icon.

Renders the shield glyph from :mod:`deskx.gui.theme.icons` as a solid
white mark on the brand indigo, then packs the frames into a multi-size
``.ico`` (Windows) and ``.png`` (source art for macOS ``.icns``).

Qt's own ICO writer only stores a single frame, so the container is
assembled by hand — Windows picks the closest frame per context, which
keeps the 16px taskbar icon crisp instead of downscaled from 256px.

Run via ``python packaging/make_icon.py`` (the build scripts do this).
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QLinearGradient, QPainter, QImage  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

from deskx.gui.theme.colors import LIGHT  # noqa: E402
from deskx.gui.theme.icons import Icon, _PATHS  # noqa: E402

# Frame sizes Windows actually asks for: list view, taskbar, shortcuts,
# alt-tab, and the extra-large explorer tile.
_SIZES = (16, 24, 32, 48, 64, 128, 256)

_GLYPH_SCALE = 0.62  # shield height relative to the tile
_CORNER_RATIO = 0.22  # squircle-ish radius, matches the app's card radius


def _shield_svg(size: int) -> bytes:
    """Solid white shield on a transparent ground."""
    body = _PATHS[Icon.SHIELD]
    markup = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}" fill="#FFFFFF" stroke="#FFFFFF" '
        'stroke-width="1.2" stroke-linejoin="round">'
        f"{body}</svg>"
    )
    return markup.encode("utf-8")


def render_frame(size: int) -> QImage:
    """Draw one square icon frame at *size* pixels."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(LIGHT.primary))
    gradient.setColorAt(1.0, QColor(LIGHT.primary_pressed))

    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    radius = size * _CORNER_RATIO
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    glyph = size * _GLYPH_SCALE
    offset = (size - glyph) / 2
    renderer = QSvgRenderer(QByteArray(_shield_svg(int(glyph))))
    renderer.render(painter, QRectF(offset, offset, glyph, glyph))

    painter.end()
    return image


def _png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def write_ico(target: Path) -> None:
    """Pack every frame into a PNG-compressed ICO container."""
    frames = [_png_bytes(render_frame(size)) for size in _SIZES]

    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = len(header) + 16 * len(frames)

    entries = bytearray()
    for size, payload in zip(_SIZES, frames):
        # 256 is encoded as 0 in the single-byte width/height fields.
        dimension = 0 if size == 256 else size
        entries += struct.pack(
            "<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(payload), offset
        )
        offset += len(payload)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bytes(header) + bytes(entries) + b"".join(frames))


def write_png(target: Path, size: int = 1024) -> None:
    """Write the master square PNG used to build the macOS icon."""
    target.parent.mkdir(parents=True, exist_ok=True)
    render_frame(size).save(str(target), "PNG")


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    here = Path(__file__).resolve().parent
    write_ico(here / "DeskX.ico")
    write_png(here / "DeskX.png")

    print(f"wrote {here / 'DeskX.ico'}")
    print(f"wrote {here / 'DeskX.png'}")
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
