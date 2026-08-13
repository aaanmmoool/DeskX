"""The one canonical description of the DeskX workflow.

Screens import these names so the breadcrumb reads the same wherever
the user happens to be.
"""

from __future__ import annotations

from typing import Final

WORKFLOW_STEPS: Final[tuple[str, ...]] = (
    "Upload",
    "Preview",
    "Configure",
    "Review",
    "Save",
    "Process",
    "Done",
)

STEP_UPLOAD: Final[int] = 0
STEP_PREVIEW: Final[int] = 1
STEP_CONFIGURE: Final[int] = 2
STEP_REVIEW: Final[int] = 3
STEP_SAVE: Final[int] = 4
STEP_PROCESS: Final[int] = 5
STEP_DONE: Final[int] = 6
