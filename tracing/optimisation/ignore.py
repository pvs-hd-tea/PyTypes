from . import Optimisation, TriggerStatus, utils
import pandas as pd


class Ignore(Optimisation):
    """
    Dumb optimisation that is always ONGOING, in order to unconditionally
    disable tracing for the relevant scope.
    """

    def __init__(self, frame: utils.FrameWithMetadata):
        super().__init__(frame)
        # By default, this optimisation is constantly active, as long as the current scope is active
        self._status = TriggerStatus.ONGOING

    def advance(
        self, current_frame: utils.FrameWithMetadata, traced: pd.DataFrame
    ) -> None:
        # Anything that indicates leaving the scope
        if current_frame.is_return():
            self._status = TriggerStatus.EXITED

    def status(self) -> TriggerStatus:
        return self._status

    def __eq__(self, o: object) -> bool:
        # Address comparison, no need to do more than shallow equality
        return isinstance(o, Ignore) and self.fwm.frame.f_code == o.fwm.frame.f_code
