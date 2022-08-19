import logging

from . import Optimisation, TriggerStatus, utils
from .utils import FrameWithMetadata

import pandas as pd
from constants import Column

logger = logging.getLogger(__name__)


class TypeStableLoop(Optimisation):
    """
    Triggers when the types of instances within loop bodies are stable for
    the given amount of iterations.
    """

    def __init__(self, frame: FrameWithMetadata, iterations_until_entry: int = 5):
        """
        @param frame Data about the very first line (e.g. `for x in xs:`) obtained from the `inspect` module
        @param iterations_until_entry The amount of iterations that shall pass until the optimisation starts firing
        """
        super().__init__(frame)
        self.until_entry = iterations_until_entry

        self._total_iterations = 0
        self._iterations_since_type_changes = 0
        self._status = TriggerStatus.INACTIVE

        self._relevant_lines: tuple[int, int] = (self.fwm.f_lineno, self.fwm.f_lineno)
        self._loop_traced_count = 0

    def status(self) -> TriggerStatus:
        return self._status

    def advance(self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame):
        # Early exit conditions: Encountering break or return
        if current_frame.is_break() or current_frame.is_return():
            logger.debug(
                f"{TypeStableLoop.__name__}: {self._status} -> EXITED: break or return"
            )
            self._status = TriggerStatus.EXITED
            return

        # We have reached the head of the loop, update iteration count
        if self._is_loop_head(current_frame):
            self._total_iterations += 1
            logger.debug(
                f"{TypeStableLoop.__name__}: Hit loop head, incremented total iteration count to {self._total_iterations}"
            )

        if self._iterations_since_type_changes < self.until_entry:
            self._when_inactive(current_frame, traced)
            logger.debug(
                f"{TypeStableLoop.__name__}: {self._status} -> INACTIVE due to being under entry count"
            )
            self._status = TriggerStatus.INACTIVE

        elif self._iterations_since_type_changes == self.until_entry:
            logger.debug(
                f"{TypeStableLoop.__name__}: {self._status} -> ENTRY due to meeting entry count"
            )
            self._when_entry(current_frame, traced)
            self._status = TriggerStatus.ENTRY

        elif self._iterations_since_type_changes > self.until_entry:
            logger.debug(
                f"{TypeStableLoop.__name__}: {self._status} -> ONGOING due to being above entry count"
            )
            self._when_ongoing(current_frame, traced)
            self._status = TriggerStatus.ONGOING

        if current_frame.f_lineno > self._relevant_lines[1]:
            logger.debug(
                f"{TypeStableLoop.__name__}: {self._status} -> EXITED due to leaving loop"
            )
            self._status = TriggerStatus.EXITED

        logger.debug(
            f"Iters since type changes is now {self._iterations_since_type_changes}"
        )
        logger.debug(f"Total iterations is now {self._total_iterations}")

    def _when_inactive(
        self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame
    ) -> None:
        # In the first iteration, update line range information
        if self._total_iterations == 0:
            begin, end = self._relevant_lines
            self._relevant_lines = begin, max(end or 0, current_frame.f_lineno)
            logger.debug(f"Updating from ({begin}, {end}) to {self._relevant_lines=}")

        # In later iterations, at the start of each iteration,
        # compare against known type information
        # and see if anything has changed by checking no more lines have been added

        # NOTE: this assumes that traced only contains unique information
        # TODO: filter by file!
        else:
            if self._is_loop_head(current_frame):
                new_loop_traced_count = (
                    traced[Column.LINENO]
                    .between(*self._relevant_lines, inclusive="both")  # type: ignore
                    .shape[0]
                )
                logger.debug(f"{new_loop_traced_count=} vs {self._loop_traced_count=}")
                if new_loop_traced_count != self._loop_traced_count:
                    # Update count since type changes
                    self._iterations_since_type_changes = 0
                    self._loop_traced_count = new_loop_traced_count

                # No types have changed, update counter
                else:
                    self._iterations_since_type_changes += 1

    def _when_entry(
        self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame
    ) -> None:
        if self._is_loop_head(current_frame):
            self._iterations_since_type_changes += 1

    def _when_ongoing(
        self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame
    ) -> None:
        if self._is_loop_head(current_frame):
            self._iterations_since_type_changes += 1

    def _is_loop_head(self, current_frame: utils.FrameWithMetadata) -> bool:
        return self.fwm.f_lineno == current_frame.f_lineno

    def __eq__(self, o: object) -> bool:
        return isinstance(o, TypeStableLoop) and self.fwm.f_lineno == o.fwm.f_lineno
