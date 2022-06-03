from . import Optimisation, TriggerStatus

class Ignore(Optimisation):
    """
    Dumb optimisation that is always ONGOING, in order to unconditionally
    disable tracing for the relevant scope.
    """
    def __init__(self):
        super().__init__()

    def advance(self, current_frame) -> None:
        pass

    def status(self) -> TriggerStatus:
        return TriggerStatus.ONGOING

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Ignore)