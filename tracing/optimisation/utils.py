from dataclasses import dataclass, field
from traceback import linecache
import logging
import functools
import io
import typing
import re
import tokenize

# Start with characters or underscore, rest is the same plus numbers
@dataclass
class FrameWithMetadata:
    # TODO: Discover typings for inspect's frames
    frame: typing.Any

    @functools.cached_property
    def tokens(self) -> list[tokenize.TokenInfo] | str:
        # Adapted from https://stackoverflow.com/a/22363519 and
        # https://stackoverflow.com/a/62167093
        filename = self.frame.f_code.co_filename
        linecache.checkcache(filename)

        line = linecache.getline(filename, self.frame.f_lineno, self.frame.f_globals)
        sio = io.StringIO(line)

        try:
            tokens = list(tokenize.generate_tokens(sio.readline))
            return tokens
        except tokenize.TokenError:
            return line

    def is_return(self) -> bool:
        if isinstance(self.tokens, list):
            return self.tokens[0].string == "return"
        return self.tokens.startswith("return")

    def is_break(self) -> bool:
        if isinstance(self.tokens, list):
            return self.tokens[0].string == "break"
        return self.tokens.startswith("break")

    def is_for_loop(self) -> bool:
        # TODO #1: this is very rudimentary, perhaps make this safer, but try to avoid runtime costs?
        # TODO #2: does this trigger on list comprehensions
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