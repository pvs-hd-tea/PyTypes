from dataclasses import dataclass, field
from traceback import linecache
import io
import typing
import re
import tokenize

# Start with characters or underscore, rest is the same plus numbers
_NAME_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_]+"
_FOR_LOOP_REGEX = re.compile(rf"for {_NAME_PATTERN} in ")


@dataclass
class FrameWithLine:
    # TODO: Discover typings for inspect's frames
    frame: typing.Any
    tokens: list[tokenize.TokenInfo]

    def __post_init__(self):
        self.line = _frame_as_line(self.frame)

    def is_return(self) -> bool:
        return self.tokens[0].string == "return"

    def is_break(self) -> bool:
        return self.tokens[0].string == "break"

    def is_for_loop(self) -> bool:
        # TODO: this is very rudimentary, perhaps make this safer, but try to avoid runtime costs?
        # TODO: does this trigger on list comprehensions
        has_for = next(
            filter(lambda tok: tok.string == "for", self.tokens), default=None
        )
        if not has_for:
            return False

        has_in = next(filter(lambda tok: tok.string == "in", self.tokens), default=None)
        if not has_in:
            return False

        (fbegin, fend), (ibegin, iend) = has_for.start, has_in.start
        return fend < iend or (fend == iend and fbegin < ibegin)


# Adapted from https://stackoverflow.com/a/22363519 and https://stackoverflow.com/a/62167093
def _frame_as_tokens(frame) -> str:
    filename = frame.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, frame.f_lineno, frame.f_globals)

    readline = io.StringIO(line).readline
    tokens = list(tokenize.generate_tokens(readline))

    return tokens
