from . import Optimisation, TriggerStatus

# TODO: Pass in trace data during first n iteration of loops
# TODO: 

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
        super().__init__()
        self.frame = frame
        self.until_entry = iterations_until_entry

        self.iterations_since_type_changes = -1

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

    def advance(self, current_frame) -> None:
        if self.frame.f_lineno == current_frame.f_lineno:
            self.iterations_since_type_changes += 1

    def __eq__(self, o: object) -> bool:
        return isinstance(o, TypeStableLoop) and self.frame.f_lineno == o.frame.f_lineno
