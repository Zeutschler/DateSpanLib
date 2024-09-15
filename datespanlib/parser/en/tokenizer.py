# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license
# ---------------------------------------------------------------
# English language tokenizer for date text parsing.
from __future__ import annotations
import sys
from enum import IntEnum
from typing import Any
import re
from datetime import datetime, time
from dateutil.parser import parse as dateutil_parse, ParserError, parserinfo


# region Tokenizer Enums and Declarations
class TokenType(IntEnum):
    # Token types for date text parsing
    EXPRESSION = -3
    START = -2
    STOP = -1

    WHITESPACE = 0

    DATE = 1  # a date parseable by dateutil.parser.parse
    TIME = 2  # a date parseable by dateutil.parser.parse
    TIME_POSTFIX = 3  # e.g. 'am', 'pm' >>> "10:00 am", "12:00 pm"
    DATE_TIME = 4  # a date parseable by dateutil.parser.parse
    DATE_TIME_RANGE = 5  # a from-to date range

    WEEKDAY = 6  # e.g. 'monday', 'tuesday', 'wednesday' >>> "Monday"
    WEEK = 7  # e.g. '1', '2', '3' >>> "Week 1"
    MONTH = 8  # e.g. 'january', 'february', 'march' >>> "January 2024"
    YEAR = 9  # e.g. '2024', '2025', '2026' >>> "January 2024"

    POSTFIX = 10  # e.g. 'days' in  "5 days"
    PERIOD_TO_DATE = 11  # e.g. 'ytd' >>> "ytd"

    LIST_DELIMITER = 20  # e.g. ',' >>> "Monday, Tuesday, Wednesday"
    RANGE_INFIX = 21  # e.g. '-', 'to', 'and' >>> "10:00 to 12:00", "between 10:00 and 12:00"
    RANGE_PREFIX = 22  # e.g. 'between', 'from' >>> "from 10:00 to 12:00", "between 10:00 and 12:00"
    OFFSET = 23  # e.g. 'next', 'last', 'previous', 'this' >>> "next week", "last month"
    #                    but also 'in', 'ago' >>> "in 5 days", "5 days ago"
    DATE_INFIX = 24  # e.g. 'of' >>> "1st of January 2024"

    NUMBER = 80
    NUMBER_POSTFIX = 81  # e.g. 'st', 'nd', 'rd', 'th' >>> "5th" or '1.' >>> "1st"

    WORD = 90  # any other word related to date text parsing
    TUPLE = 91
    UNKNOWN = 99

    def __str__(self):
        return self.name


class TokenSubType(IntEnum):
    POSITIVE = 1
    NEGATIVE = -1
    UNDEFINED = 0

    DELIMITER = 1  # e.g. ',' >>> "Monday, Tuesday" or ';' >>> "Monday; Tuesday"

    MILLISECOND = 10  # e.g. 'ms', 'millisecond', 'milliseconds' >>> "5 milliseconds"
    SECOND = 11  # e.g. 's', 'sec', 'secs', 'second', 'seconds' >>> "5 seconds"
    MINUTE = 12  # e.g. 'm', 'min', 'mins', 'minute', 'minutes' >>> "5 minutes"
    HOUR = 13  # e.g. 'h', 'hr', 'hrs', 'hour', 'hours' >>> "5 hours"
    DAY = 14  # e.g. 'd', 'day', 'days' >>> "5 days"
    WEEK = 15  # e.g. 'w', 'wk', 'wks', 'week', 'weeks' >>> "5 weeks"
    MONTH = 16  # e.g. 'mo', 'month', 'months' >>> "5 months"
    YEAR = 17  # e.g. 'y', 'yr', 'yrs', 'year', 'years' >>> "5 years"
    QUARTER = 18  # e.g. 'q', 'qtr', 'qtrs', 'quarter', 'quarters' >>> "5 quarters"

    SINCE = 20  # e.g. 'since' >>> "since 5 days"

    UNKNOWN = 99

    def __str__(self):
        return self.name

ALIASES_ = {
    # weekdays
    'tue': 'tuesday',
    'wed': 'wednesday',
    'thu': 'thursday',
    'fri': 'friday',
    'sat': 'saturday',
    'sun': 'sunday',

    'mo': 'monday',
    'tu': 'tuesday',
    'we': 'wednesday',
    'th': 'thursday',
    'fr': 'friday',
    'sa': 'saturday',
    'su': 'sunday',

    # months
    'jan': 'january',
    'feb': 'february',
    'mar': 'march',
    'apr': 'april',
    'may': 'may',
    'jun': 'june',
    'jul': 'july',
    'aug': 'august',
    'sep': 'september',
    'sept': 'september',
    'oct': 'october',
    'nov': 'november',
    'dec': 'december',

    # postfixes
    's': 'second',
    'sec': 'second',
    'secs': 'second',
    'second': 'second',
    'seconds': 'second',

    'm': 'minute',
    'min': 'minute',
    'mins': 'minute',
    'minute': 'minute',
    'minutes': 'minute',

    'h': 'hour',
    'hr': 'hour',
    'hrs': 'hour',
    'hour': 'hour',
    'hours': 'hour',

    'd': 'day',
    'day': 'day',
    'days': 'day',

    'mon': 'month',
    'month': 'month',
    'months': 'month',

    'y': 'year',
    'yr': 'year',
    'yrs': 'year',
    'year': 'year',
    'years': 'year',

    'q': 'quarter',
    'qtr': 'quarter',
    'qrt': 'quarter', # catch typo
    'qtrs': 'quarter',
    'quarter': 'quarter',
    'quarters': 'quarter',

    'w': 'week',
    'wk': 'week',
    'wks': 'week',
    'week': 'week',
    'weeks': 'week',

    # others
    # time related
    'a.m.': 'am',
    'am': 'am',
    'p.m.': 'pm',
    'pm': 'pm',

    # offsets
    'nxt': 'next',
    'previous': 'last',
    'prev': 'last',
    'prv': 'last',
    'prev.': 'last',
    'lst': 'last',
    'ths': 'this',
    'actual': 'this',
    'act': 'this',
    'in': 'in',
    'ago': 'ago',
    'of': 'of',
    'btw': 'between',
    'btwn': 'between',
    'frm': 'from',
    'to': 'to',
    'and': 'and',
    'nd': 'and',
    'n': 'and',
    'after': 'after',

    'bef': 'before',
    'befor': 'before',

    'until': 'until',
    'till': 'until',
    'since': 'since',
    'by': 'by',

    # time related
    'half': 'half',

    # period  to date
    'ytd': 'ytd',
    'mtd': 'mtd',
    'qtd': 'qtd',
    'wtd': 'wtd',

}
# add abbreviation variants with a dot at the end
ALIASES = {k: v for k, v in ALIASES_.items()}
all_aliases = [(k, v) for k, v in ALIASES_.items()]
for k, v in all_aliases:
    if not k.endswith('.') and (k + ".") not in ALIASES:
        ALIASES[k + "."] = v

KEYWORDS = {
    # weekdays
    "monday": ['monday', 1, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "tuesday": ['tuesday', 2, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "wednesday": ['wednesday', 3, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "thursday": ['thursday', 4, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "friday": ['friday', 5, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "saturday": ['saturday', 6, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "sunday": ['sunday', 7, TokenType.WEEKDAY, TokenSubType.UNDEFINED],

    "january": ['january', 1, TokenType.MONTH, TokenSubType.UNDEFINED],
    "february": ['february', 2, TokenType.MONTH, TokenSubType.UNDEFINED],
    "march": ['march', 3, TokenType.MONTH, TokenSubType.UNDEFINED],
    "april": ['april', 4, TokenType.MONTH, TokenSubType.UNDEFINED],
    "may": ['may', 5, TokenType.MONTH, TokenSubType.UNDEFINED],
    "june": ['june', 6, TokenType.MONTH, TokenSubType.UNDEFINED],
    "july": ['july', 7, TokenType.MONTH, TokenSubType.UNDEFINED],
    "august": ['august', 8, TokenType.MONTH, TokenSubType.UNDEFINED],
    "september": ['september', 9, TokenType.MONTH, TokenSubType.UNDEFINED],
    "october": ['october', 10, TokenType.MONTH, TokenSubType.UNDEFINED],
    "november": ['november', 11, TokenType.MONTH, TokenSubType.UNDEFINED],
    "december": ['december', 12, TokenType.MONTH, TokenSubType.UNDEFINED],

    # postfixes
    "second": ['second', None, TokenType.POSTFIX, TokenSubType.SECOND],
    "minute": ['minute', None, TokenType.POSTFIX, TokenSubType.MINUTE],
    "hour": ['hour', None, TokenType.POSTFIX, TokenSubType.HOUR],
    "day": ['day', None, TokenType.POSTFIX, TokenSubType.DAY],
    "month": ['month', None, TokenType.POSTFIX, TokenSubType.MONTH],
    "year": ['year', None, TokenType.POSTFIX, TokenSubType.YEAR],
    "quarter": ['quarter', None, TokenType.POSTFIX, TokenSubType.QUARTER],
    "week": ['week', None, TokenType.POSTFIX, TokenSubType.WEEK],

    "am": ['am', 0, TokenType.TIME_POSTFIX, TokenSubType.UNDEFINED],
    "pm": ['pm', 12, TokenType.TIME_POSTFIX, TokenSubType.UNDEFINED],

    # others
    "since": ['since', 1, TokenType.OFFSET, TokenSubType.SINCE],
    "over": ['next', 1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "next": ['next', 1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "last": ['last', -1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "previous": ['previous', -1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "this": ['this', 0, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "in": ['in', 1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "ago": ['ago', 1, TokenType.OFFSET, TokenSubType.UNDEFINED],
    "of": ['of', None, TokenType.DATE_INFIX, TokenSubType.UNDEFINED],

    ",": [',', None, TokenType.LIST_DELIMITER, TokenSubType.DELIMITER],
    ";": [',', None, TokenType.STOP, TokenSubType.DELIMITER],
    "-": ['-', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED],
    "to": ['to', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED],
    "and": ['and', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED],
    "between": ['between', None, TokenType.RANGE_PREFIX, TokenSubType.UNDEFINED],

    "now": ['now', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED],
    "tomorrow": ['tomorrow', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED],
    "today": ['today', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED],
    "yesterday": ['yesterday', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED],

    "ytd": ['ytd', None, TokenType.PERIOD_TO_DATE, TokenSubType.YEAR],
    "mtd": ['mtd', None, TokenType.PERIOD_TO_DATE, TokenSubType.MONTH],
    "qtd": ['qtd', None, TokenType.PERIOD_TO_DATE, TokenSubType.QUARTER],
    "wtd": ['wtd', None, TokenType.PERIOD_TO_DATE, TokenSubType.WEEK],

}

ORDINAL_POSTFIXES = ['st', 'nd', 'rd', 'th']
CALENDER_KEYWORDS = [TokenType.WEEKDAY, TokenType.MONTH, TokenType.YEAR]
DATETIME_REFERENCE = [TokenType.DATE, TokenType.TIME, TokenType.DATE_TIME,
                      TokenType.WEEKDAY, TokenType.WEEK, TokenType.MONTH, TokenType.YEAR]
RE_TIME_FORMAT = re.compile(r"^([0-9]|[0-1][0-9]|2[0-3]):[0-5][0-9]?(:[0-5][0-9])?(?:[.,][0-9]+)?$")
# endregion



class Token:
    """Represents a token in a date text."""

    def __init__(self, text: str, token_type=TokenType.UNKNOWN, token_sub_type=TokenSubType.UNDEFINED, value=None,
                 raw_text=None):
        self.type: TokenType = token_type
        self.sub_type: TokenSubType = token_sub_type
        self.text: str = text
        self.raw_text: str = raw_text if raw_text else text
        self.ordinal: int = 0
        self.value: Any = value
        self.priority: int = 0

    def __str__(self):
        return f"{'.' * (30 - (len(self.type.name) + len(self.sub_type.name)))}{self.type}.{self.sub_type}: '{self.text}' , value:={self.value}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Token):
            # note: raw_text and text are not considered for equality
            return self.type == other.type and self.sub_type == other.sub_type and self.value == other.value
        return False


class TokenList:
    """A navigable list of tokens."""

    def __init__(self, tokens: list[Token] | None = None):
        self.n: int = 0
        if tokens is None:
            self._tokens: list[Token] = []
        else:
            self._tokens: list[Token] = tokens
        self.rebuild_ordinals()

    def rebuild_ordinals(self):
        for i, t in enumerate(self._tokens):
            t.ordinal= 1

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self) -> Token:
        if self.n < len(self._tokens):
            item = self._tokens[self.n]
            self.n += 1
            return item
        else:
            raise StopIteration

    @property
    def tokens(self) -> list[Token]:
        return self._tokens

    def pop(self, index, count:int = 1)-> Token | list[Token]:
        if count == 1:
            item = self._tokens.pop(index)
        else:
            item = self._tokens[index:index + count]
            for _ in range(count):
                self._tokens.pop(index)
        self.rebuild_ordinals()
        return item

    # def peek(self) -> Token:
    #     if self.n < len(self):
    #         return self[self.n]
    #     raise IndexError("End of list reached.")

    # def next(self):
    #     if self.iter_index < len(self):
    #         self.iter_index += 1
    #         return self[self.iter_index - 1]
    #     else:
    #         raise IndexError("End of list reached.")
    #
    # def previous(self):
    #     if self.iter_index > 0:
    #         self.iter_index -= 1
    #         return self[self.iter_index]
    #     else:
    #         raise IndexError("Start of list reached.")

    def remove(self, __value):
        if isinstance(__value, Token):
            self._tokens.remove(__value)
            self.rebuild_ordinals()
        elif isinstance(__value, int):
            self._tokens.pop(__value)
            self.rebuild_ordinals()
        else:
            raise ValueError("Invalid value type.")

    def find_first(self, text = None, type: TokenType | list | tuple | None = None,
             sub_type: TokenSubType | list | tuple | None = None,
             start: int = 0, end:int = sys.maxsize) -> (bool, int, Token | None):
        if start >= len(self._tokens):
            return False, -1, None

        # converts single values to lists
        if text is not None:
            if isinstance(text, str):
                text = [text,]
        if type is not None:
            if isinstance(type, TokenType):
                type = [type, ]
        if sub_type is not None:
            if isinstance(sub_type, TokenSubType):
                sub_type = [sub_type, ]

        # check texts
        if text is not None:
            for i, token in enumerate(self._tokens[start:end]):
                if token.text in text:
                    if type is not None and token.type in type:
                        continue
                    if sub_type is not None and token.sub_type not in sub_type:
                        continue
                    return True, i, token
        # check token types
        if type is not None:
            for i, token in enumerate(self._tokens[start:end]):
                if token.type in type:
                    if sub_type is not None and token.sub_type not in sub_type:
                        continue
                    return True, i, token
        # check token subtypes
        if sub_type is not None:
            for i, token in enumerate(self._tokens[start:end]):
                if token.sub_type in sub_type:
                    return True, i, token
        return False, -1, None


    def offset(self, offset: int) -> Token | None:
        if -1 < self.n + offset < len(self._tokens):
            return self._tokens[self.n + offset]
        else:
            return None

    def remaining(self):
        return self._tokens[self.n:]

    def has_next(self):
        return self.n < len(self._tokens)

    def has_previous(self):
        return self.n > 0

    def __eq__(self, other):
        if isinstance(other, TokenList):
            if len(self) != len(other):
                return False
            for s, o in zip(self._tokens, other._tokens):
                if s != o:
                    return False
            return True
        return False

    def __len__(self):
        return len(self._tokens)

    def to_text(self):
        """Converts the token list back to a text string."""
        text = " ".join([t.raw_text for t in self._tokens])
        text = text.replace(" ,", ",")
        text = text.replace(" ;", ";")
        return text

    def __str__(self):
        tokens = []
        tokens.append(f"TokenList({len(self)}): ")
        for i, t in enumerate(self._tokens):
            tokens.append(f"{i:3d}: {t.type}.{t.sub_type}: '{t.text}'= {t.value}")
        return f"\n".join(tokens)

    def __repr__(self):
        return self.__str__()

    def __contains__(self, item):
        if isinstance(item, Token):
            return item in self._tokens
        if isinstance(item, TokenType):
            return item in [t.type for t in self._tokens]
        if isinstance(item, TokenSubType):
            return item in [t.sub_type for t in self._tokens]
        if isinstance(item, str):
            return item in [t.text for t in self._tokens]
        return False

    def __getitem__(self, item) -> Token | TokenList:
        if isinstance(item, Token):
            return self._tokens[self._tokens.index(item)]
        if isinstance(item, TokenType):
            for t in self._tokens:
                if t.type == item:
                    return t
        if isinstance(item, TokenSubType):
            for t in self._tokens:
                if t.sub_type == item:
                    return t
        if isinstance(item, str):
            for t in self._tokens:
                if t.text == item:
                    return t
        if isinstance(item, int):
            return self._tokens[item]
        if isinstance(item, slice):
            return TokenList(self._tokens[item])
        raise ValueError("Invalid item type.")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._tokens[key] = value
            self._tokens[key].ordinal = key
        else:
            raise ValueError("Invalid key type.")

    def index(self, item, start:int=0, stop:int= sys.maxsize) -> int:
        if isinstance(item, Token):
            return self._tokens.index(item, start, stop)
        elif isinstance(item, TokenType):
            for i, t in enumerate(self._tokens):
                if start <= i <= stop and t.type == item:
                    return i
        elif isinstance(item, TokenSubType):
            for i, t in enumerate(self._tokens):
                if start <= i <= stop and t.sub_type == item:
                    return i
        elif isinstance(item, str):
            for i, t in enumerate(self._tokens):
                if start <= i <= stop and t.text == item:
                    return i
        return -1


class Tokenizer:
    """Tokenizes a date text into a list of tokens."""

    @staticmethod
    def tokenize(text: str, parser_info: parserinfo | None = None) -> TokenList:

        # 1st run - raw token processing
        stack = []
        text_tokens = Tokenizer.split_tokens(text)
        tokens: list[Token] = []
        for text in text_tokens:
            if text == "":
                continue
            while len(stack) > 0:
                tokens.append(stack.pop())

            # extract delimiters
            if text.endswith(";"):
                stack.append(Token(";", token_type=TokenType.STOP, token_sub_type=TokenSubType.DELIMITER))
                text = text[:-1]
                if text == "":
                    continue
            if text.endswith(","):
                stack.append(Token(",", token_type=TokenType.LIST_DELIMITER, token_sub_type=TokenSubType.DELIMITER))
                text = text[:-1]
                if text == "":
                    continue

            # translate aliases and process date text keywords
            raw_text = text
            text = ALIASES.get(text, text)
            if text in KEYWORDS:
                text, value, token_type, sub_type = KEYWORDS[text]
                tokens.append(
                    Token(text=text, token_type=token_type, token_sub_type=sub_type, value=value, raw_text=raw_text))
                continue

            if text.isdigit():
                number = int(text)
                if 1900 <= number <= 2100:
                    tokens.append(Token(text, TokenType.YEAR, value=number))
                else:
                    tokens.append(Token(text, TokenType.NUMBER, value=number))
                continue

            if text[0].isdigit():
                # check for ordinal dates like '1.' in '1. of January'
                if len(text) > 1:
                    postfix = text[-1:]
                    if postfix == ".":
                        number_text = text[:-1]
                        if number_text.isdigit():
                            tokens.append(Token(number_text, TokenType.NUMBER, value=int(number_text)))
                            tokens.append(Token(postfix, TokenType.NUMBER_POSTFIX))
                            continue
                # check for ordinal date or week numbers like '1st', '2nd', '3rd', '4th', ...
                if len(text) > 2:
                    postfix = text[-2:]
                    if postfix in ORDINAL_POSTFIXES:
                        number_text = text[:-2]
                        if number_text.isdigit():
                            tokens.append(Token(number_text, TokenType.NUMBER, value=int(number_text)))
                            tokens.append(Token(postfix, TokenType.NUMBER_POSTFIX))
                            continue

            # check for valid time and date tokens
            if RE_TIME_FORMAT.match(text):
                tokens.append(Token(text, TokenType.TIME, value=dateutil_parse(text, parser_info, fuzzy=True).time()))
                continue
            try:
                date = dateutil_parse(text, parser_info, fuzzy=True)
                if date.time() == time(0, 0, 0):
                    tokens.append(Token(text, TokenType.DATE, value=date))
                else:
                    tokens.append(Token(text, TokenType.DATE_TIME, value=date))
                continue
            except (ParserError, OverflowError):
                # errors get ignored, and the text turns into an unknown token
                pass

            token = Token(text, TokenType.UNKNOWN)
            tokens.append(token)

        # push remaining stack to tokens
        if len(stack) > 0:
            tokens.extend(stack)

        # Post-processing...
        # ...if just 1 token text
        if len(tokens) == 1:
            token = tokens[0]
            if token.type in CALENDER_KEYWORDS:  # month or weekday names or year number
                token.type = TokenType.DATE_TIME_RANGE

        return TokenList(tokens)

    @staticmethod
    def split_tokens(text) -> list[str]:
        if "\n" in text:
            text = " ".join(text.splitlines())  # multi-line text to single line
        text = text.lower().strip()
        if "_" in text and " " not in text:  # replace underscores with spaces, e.g. 'cdf.last_month'
            text = text.replace("_", " ")
        if " " in text:
            tokens = text.split()
            tokens = [t for t in tokens if t != ""]
        else:
            tokens = [text, ]
        return tokens
