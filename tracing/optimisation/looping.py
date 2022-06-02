from . import Optimisation, TriggerStatus

class TypeStableLoopOpt(Optimisation):
    """
    Triggers when the types of instances within loop bodies are stable for 
    the given amount of iterations.
    """
    def __init__(self, iterations_until_entry = 5):
        super().__init__()
        self.iterations_since_type_changes = 0
        self.until_entry = iterations_until_entry

    def status(self) -> TriggerStatus:
        if self.iterations_since_type_changes < self.until_entry:
            return TriggerStatus.INACTIVE
        elif self.iterations_since_type_changes == self.until_entry:
            return TriggerStatus.ENTRY
        elif self.iterations_since_type_changes > self.until_entry:
            return TriggerStatus.ONGOING

        # NOTE: Technically unreachable code right now, but perhaps a future change will 
        # NOTE: create a need for an explicit exit.
        else:
            return TriggerStatus.EXIT

    def advance(self) -> None:
        self.iterations_since_type_changes += 1