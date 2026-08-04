"""QThread-based background worker for processing jobs.

This is the **only** module that bridges PySide6 signals with the
processing engine.  The actual work happens inside
:class:`~deskx.processing.job.ProcessingJob`, which has no Qt
dependency.

Usage in the GUI layer::

    worker = BackgroundWorker(job_config)
    worker.progress.connect(on_progress)
    worker.completed.connect(on_done)
    worker.failed.connect(on_error)
    worker.start()
    # To cancel:
    worker.cancel()
"""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QThread, Signal

from deskx.core.exceptions import CancellationError
from deskx.processing.job import JobConfig, ProcessingJob, ProgressUpdate
from deskx.services.progress import CompletionEvent, ErrorEvent, ProgressEvent

logger = logging.getLogger(__name__)


class BackgroundWorker(QThread):
    """Runs a :class:`ProcessingJob` off the main thread.

    Signals
    -------
    progress(ProgressEvent)
        Emitted at each pipeline stage.
    completed(CompletionEvent)
        Emitted on successful completion.
    failed(ErrorEvent)
        Emitted on error or cancellation.
    """

    progress = Signal(ProgressEvent)
    completed = Signal(CompletionEvent)
    failed = Signal(ErrorEvent)

    def __init__(
        self,
        config: JobConfig,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._config = config
        self._cancel_event = threading.Event()

    # ── Public API ──────────────────────────────────────────────────

    def cancel(self) -> None:
        """Request cancellation of the running job."""
        self._cancel_event.set()

    # ── QThread override ────────────────────────────────────────────

    def run(self) -> None:  # noqa: D401 — Qt convention
        """Execute the processing pipeline (runs on worker thread)."""
        job = ProcessingJob(
            config=self._config,
            on_progress=self._on_progress,
            cancel_event=self._cancel_event,
        )
        try:
            report = job.run()
            self.completed.emit(
                CompletionEvent(
                    message="Processing complete.",
                    report_json=report.to_json(),
                )
            )
        except CancellationError:
            self.failed.emit(
                ErrorEvent(
                    message="Processing was cancelled.",
                    is_cancellation=True,
                )
            )
        except Exception as exc:
            logger.exception("Background worker failed")
            self.failed.emit(
                ErrorEvent(message=str(exc))
            )

    # ── Callback bridge ─────────────────────────────────────────────

    def _on_progress(self, update: ProgressUpdate) -> None:
        """Bridge domain progress → Qt signal."""
        self.progress.emit(
            ProgressEvent(
                message=update.message,
                percent=update.percent,
            )
        )
