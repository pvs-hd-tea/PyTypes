import logging
import inspect

import pandas as pd

from . import Optimisation, TriggerStatus, utils


class Ignore(Optimisation):
    """
    Dumb optimisation that is always ONGOING, in order to unconditionally
    disable tracing for the relevant scope.
    """

    def __init__(self, frame: utils.FrameWithMetadata):
        super().__init__(frame)
        # By default, this optimisation is constantly active, as long as the current scope is active
        self._status = TriggerStatus.ONGOING

    def advance(self, current_frame: utils.FrameWithMetadata, _: pd.DataFrame) -> None:
        # If we reach a stack frame that is under the earliest stack frame we want to ignore
        if (
            self.fwm._frame.f_back is not None
            and self.fwm._frame.f_back == current_frame._frame
        ):
            logging.debug(
                f"Switched Ignore to EXITED with {inspect.getframeinfo(current_frame._frame)}"
            )
            self._status = TriggerStatus.EXITED

    def status(self) -> TriggerStatus:
        return self._status

    def __eq__(self, o: object) -> bool:
        # Address comparison, no need to do more than shallow equality
        return isinstance(o, Ignore) and self.fwm._frame.f_code == o.fwm._frame.f_code
