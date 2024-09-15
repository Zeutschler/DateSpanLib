# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license

from __future__ import annotations
from dateutil.parser import parserinfo

from datespanlib.date_span import DateSpan
from datespanlib.date_span_set import DateSpanSet

__author__ = "Thomas Zeutschler"
__version__ = "0.1.5"
__license__ = "MIT"
VERSION = __version__

__all__ = [
    "DateSpanSet",
    "DateSpan",
    "parse",
    "VERSION"
]


def parse(datespan_text: str, language: str | None = "en", parser_info: parserinfo | None = None) -> DateSpanSet:
    """
    Creates a new DateSpanSet instance and parses the given text into a set of DateSpan objects.

    Arguments:
        datespan_text: The date span text to parse, e.g. 'last month', 'next 3 days', 'yesterday' or 'Jan 2024'.
        language: (optional) An ISO 639-1 2-digit compliant language code for the language of the text to parse.
        parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
            datespan_text. If not defined, the default parser of the dateutil library will be used.

    Returns:
        The DateSpanSet instance contain 0 to N DateSpan objects derived from the given text.

    Examples:
        >>> DateSpanSet.evaluate('last month')  # if today would be in February 2024
        DateSpanSet([DateSpan(datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 31, 23, 59, 59, 999999))])
    """
    return DateSpanSet(datespan_text, language, parser_info)
