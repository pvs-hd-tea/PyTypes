from dataclasses import dataclass
from traceback import linecache  # type: ignore
import functools
import io
import typing
import tokenize


@dataclass
class FrameWithMetadata:
    """A wrapper dataclass that takes the current frame and checks properties of the frame's state"""
    _frame: typing.Any

    @functools.cached_property
    def co_filename(self) -> str:
        """Get the filename of the code referenced by the frame"""
        return self._frame.f_code.co_filename

    @functools.cached_property
    def f_lineno(self) -> int:
        """Get the line number referenced by the frame"""
        return self._frame.f_lineno

    @functools.cached_property
    def tokens(self) -> list[tokenize.TokenInfo] | str:
        """Get a representation of the line currently being executed"""
        # Adapted from https://stackoverflow.com/a/22363519 and
        # https://stackoverflow.com/a/62167093
        filename = self._frame.f_code.co_filename
        linecache.checkcache(filename)

        line = linecache.getline(filename, self._frame.f_lineno, self._frame.f_globals)
        sio = io.StringIO(line)

        try:
            tokens = list(tokenize.generate_tokens(sio.readline))
            return tokens
        except tokenize.TokenError:
            return line

    def is_return(self) -> bool:
        """Return True if the frame represents a return statement"""
        if isinstance(self.tokens, list):
            return self.tokens[0].string == "return"
        return self.tokens.startswith("return")

    def is_break(self) -> bool:
        """Return True if the frame represents a break statement"""
        if isinstance(self.tokens, list):
            return self.tokens[0].string == "break"
        return self.tokens.startswith("break")

    def is_for_loop(self) -> bool:
        """Return True if the frame represents a for loop"""
        if isinstance(self.tokens, list):
            fors = filter(lambda tok: tok.string == "for", self.tokens)
            has_for = next(fors, None)
            if not has_for:
                return False

            ins = filter(lambda tok: tok.string == "in", self.tokens)
            has_in = next(ins, None)
            if not has_in:
                return False

            (fbegin, fend), (ibegin, iend) = has_for.start, has_in.start
            return fend < iend or (fend == iend and fbegin < ibegin)

        return "for" in self.tokens and "in" in self.tokens
