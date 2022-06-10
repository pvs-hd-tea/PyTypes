from . import Optimisation, TriggerStatus, utils
import constants

import pandas as pd


class TypeStableLoop(Optimisation):
    """
    Triggers when the types of instances within loop bodies are stable for
    the given amount of iterations.
    """

    def __init__(self, frame, iterations_until_entry: int = 5):
        """
        @param frame Data about the very first line (e.g. `for x in xs:`) obtained from the `inspect` module
        @param iterations_until_entry The amount of iterations that shall pass until the optimisation starts firing
        """
        super().__init__(frame)
        self.until_entry = iterations_until_entry

        self._total_iterations = -1
        self._iterations_since_type_changes = 0
        self._status = TriggerStatus.INACTIVE

        self._relevant_lines = (self.fwm.frame.f_lineno, None)
        self._loop_traced_count = None

    def status(self) -> TriggerStatus:
        return self._status

    def advance(self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame):
        # Early exit conditions: Encountering break or return
        if current_frame.is_break() or current_frame.is_return():
            self._status = TriggerStatus.EXITED
            return

        # We have reached the head of the loop, update iteration count
        if self._is_loop_head(current_frame):
            self._total_iterations += 1

        if self._iterations_since_type_changes < self.until_entry:
            self._when_inactive(current_frame, traced)
            return TriggerStatus.INACTIVE

        elif self._iterations_since_type_changes == self.until_entry:
            self._when_entry(current_frame, traced)
            return TriggerStatus.ENTRY

        elif self._iterations_since_type_changes > self.until_entry:
            self._when_ongoing(current_frame, traced)
            return TriggerStatus.ONGOING

        # NOTE: Technically unreachable code right now, but perhaps a
        # NOTE: future change will create a need for an explicit exit.
        else:
            return TriggerStatus.EXITED

    def _when_inactive(
        self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame
    ) -> None:
        # In the first iteration, update line range information
        if self._total_iterations == 0:
            begin, _ = self._relevant_lines
            self._relevant_lines = begin, current_frame.frame.f_lineno

        # In later iterations, at the start of each iteration,
        # compare against known type information
        # and see if anything has changed by checking no more lines have been added

        # NOTE: this assumes that traced only contains unique information
        # TODO: filter by file!
        else:
            if self._is_loop_head(current_frame):
                new_loop_traced_count = (
                    traced[constants.TraceData.LINENO]
                    .between(*self._relevant_lines, inclusive="both")
                    .shape[0]
                )
                if (
                    self._loop_traced_count is not None
                    and new_loop_traced_count > self._loop_traced_count
                ):
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
        return self.fwm.frame.f_lineno == current_frame.frame.f_lineno

    def __eq__(self, o: object) -> bool:
        return (
            isinstance(o, TypeStableLoop)
            and self.fwm.frame.f_lineno == o.fwm.frame.f_lineno
        )
