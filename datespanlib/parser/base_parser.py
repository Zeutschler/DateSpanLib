# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license

from abc import ABC, abstractmethod
from dateutil.parser import parserinfo

from datespanlib.date_span import DateSpan


class DateTextLanguageParser(ABC):
    """Base class for language specific date text parsing."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Returns the ISO 639-1 language code of the parser."""
        pass

    @abstractmethod
    def evaluate(self, text: str, parser_info: None | parserinfo = None) -> DateSpan | list[DateSpan]:
        """
        Parses a date text string into a list of DateSpans, each containing a (`datetime`, `datetime`) time-span tuples.

        Arguments:
            text: The date text string to parse.
            parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                datespan_text. If not defined, the default parser of the dateutil library will be used.

        Returns:
            A list of DateSpan objects or None. If None is returned, the text could not be parsed.
        """
        pass

    @property
    @abstractmethod
    def message(self) -> str:
        """Returns information about the last failing parsing operation."""
        pass