from enum import IntEnum
from typing import Any
import re
from datetime import datetime, time
from dateutil.parser import parse as dateutil_parse, ParserError, parserinfo


class TokenType(IntEnum):
    # Token types for date text parsing
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

    LIST_DELIMITER = 20  # e.g. ',' >>> "Monday, Tuesday, Wednesday"
    RANGE_INFIX = 21  # e.g. '-', 'to', 'and' >>> "10:00 to 12:00", "between 10:00 and 12:00"
    RANGE_PREFIX = 22  # e.g. 'between', 'from' >>> "from 10:00 to 12:00", "between 10:00 and 12:00"
    OFFSET = 23  # e.g. 'next', 'last', 'previous', 'this' >>> "next week", "last month"
    #                    but also 'in', 'ago' >>> "in 5 days", "5 days ago"
    DATE_INFIX = 24  # e.g. 'of' >>> "1st of January 2024"

    NUMBER = 80
    NUMBER_POSTFIX = 81  # e.g. 'st', 'nd', 'rd', 'th' >>> "5th" or '1.' >>> "1st"

    WORD = 90   # any other word related to date text parsing
    TUPLE = 91
    UNKNOWN = 99

    def __str__(self):
        return self.name

class TokenSubType(IntEnum):
    POSITIVE = 1
    NEGATIVE = -1
    UNDEFINED = 0

    MILLISECOND = 10  # e.g. 'ms', 'millisecond', 'milliseconds' >>> "5 milliseconds"
    SECOND = 11  # e.g. 's', 'sec', 'secs', 'second', 'seconds' >>> "5 seconds"
    MINUTE = 12  # e.g. 'm', 'min', 'mins', 'minute', 'minutes' >>> "5 minutes"
    HOUR = 13  # e.g. 'h', 'hr', 'hrs', 'hour', 'hours' >>> "5 hours"
    DAY = 14  # e.g. 'd', 'day', 'days' >>> "5 days"
    WEEK = 15  # e.g. 'w', 'wk', 'wks', 'week', 'weeks' >>> "5 weeks"
    MONTH = 16  # e.g. 'mo', 'month', 'months' >>> "5 months"
    YEAR = 17  # e.g. 'y', 'yr', 'yrs', 'year', 'years' >>> "5 years"
    QUARTER = 18  # e.g. 'q', 'qtr', 'qtrs', 'quarter', 'quarters' >>> "5 quarters"

    UNKNOWN = 99


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
    'p.m.': 'pm',

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
}
# add abbreviation variants with a dot at the end
ALIASES = {k: v for k, v in ALIASES_.items()}
for k,v in ALIASES_.items():
    if not k.endswith('.') and k != v:
        ALIASES[k + "."] = v


# Prepositions and Conjunctions Related to Time
#------------------------------------------------
# Before – Refers to a time earlier than a specific point (e.g., "before 5 PM").
# After – Indicates a time following a specific point (e.g., "after the meeting").
# During – Refers to the time something happens within a specific period (e.g., "during the conference").
# Until/Till – Specifies a point in time up to which something continues (e.g., "until 6 PM").
# Since – Refers to the starting point of a period of time (e.g., "since Monday").
# From – Indicates the starting time of an event or duration (e.g., "from 3 PM").
# To – Used to show the ending time in a duration (e.g., "from 3 PM to 5 PM").
# Between – Refers to the time separating two points (e.g., "between 1 and 2 PM").
# By – Means no later than a specific time (e.g., "by 5 PM").
# Within – Indicates a time period that does not exceed a given limit (e.g., "within an hour").
# About – Refers to an approximate time (e.g., "about 3 PM").
# In – Indicates a time in the future (e.g., "in an hour").
# On – Refers to a specific day or date (e.g., "on Monday").
# At – Refers to a specific point in time (e.g., "at 6 PM").
# Ago – Refers to a time that has passed (e.g., "three days ago").

# Time-Related Adverbs
#------------------------------------------------
# Today – Refers to the present day.
# Yesterday – Refers to the day before today.
# Tomorrow – Refers to the day after today.
# Now – Refers to the present moment.
# Then – Refers to a specific time in the past or future.
# Soon – Refers to a time shortly after the present moment.
# Later – Refers to a time after a specific point.
# Earlier – Refers to a time before a specific point.
# Next – Refers to the subsequent occurrence of a time period or event (e.g., "next week").
# Previous – Refers to the time or event before the current one (e.g., "previous month").
# Recently – Refers to a short time ago.
# Lately – Refers to the recent past.

# Time Indicators
#------------------------------------------------
# Second – A unit of time, 1/60th of a minute.
# Minute – A unit of time, 1/60th of an hour.
# Hour – A unit of time, equal to 60 minutes.
# Day – A 24-hour period.
# Week – A period of 7 days.
# Month – A period typically consisting of 30 or 31 days.
# Year – A period of 12 months or 365 days.
# Decade – A period of 10 years.
# Century – A period of 100 years.
# Millennium – A period of 1,000 years.
# Specific Time Expressions
# AM – Refers to the time between midnight and noon.
# PM – Refers to the time between noon and midnight.
# Noon – Refers to 12:00 PM (midday).
# Midnight – Refers to 12:00 AM (the beginning of a new day).
# Quarter past – 15 minutes after the hour (e.g., "quarter past 2").
# Half past – 30 minutes after the hour (e.g., "half past 3").
# Quarter to – 15 minutes before the hour (e.g., "quarter to 5").




KEYWORDS = {
    # weekdays
    "monday": ['monday', 1, TokenType.WEEKDAY, TokenSubType.UNDEFINED],
    "tuesday": ['tuesday', 2, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],
    "wednesday": ['wednesday', 3, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],
    "thursday": ['thursday', 4, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],
    "friday": ['friday', 5, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],
    "saturday": ['saturday', 6, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],
    "sunday": ['sunday', 7, TokenType.WEEKDAY, TokenSubType.UNDEFINED ],

    "january": ['january', 1, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "february": ['february', 2, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "march": ['march', 3, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "april": ['april', 4, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "may": ['may', 5, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "june": ['june', 6, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "july": ['july', 7, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "august": ['august', 8, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "september": ['september', 9, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "october": ['october', 10, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "november": ['november', 11, TokenType.MONTH, TokenSubType.UNDEFINED ],
    "december": ['december', 12, TokenType.MONTH, TokenSubType.UNDEFINED ],

    # postfixes
    "second": ['second', None, TokenType.POSTFIX, TokenSubType.SECOND],
    "minute": ['minute', None, TokenType.POSTFIX, TokenSubType.MINUTE],
    "hour": ['hour', None, TokenType.POSTFIX, TokenSubType.HOUR],
    "day": ['day', None, TokenType.POSTFIX, TokenSubType.DAY],
    "month": ['month', None, TokenType.POSTFIX, TokenSubType.MONTH],
    "year": ['year', None, TokenType.POSTFIX, TokenSubType.YEAR],
    "quarter": ['quarter', None, TokenType.POSTFIX, TokenSubType.QUARTER],
    "week": ['week', None, TokenType.POSTFIX, TokenSubType.WEEK],

    "am": ['am', 0, TokenType.TIME_POSTFIX, TokenSubType.UNDEFINED ],
    "pm": ['pm', 12, TokenType.TIME_POSTFIX, TokenSubType.UNDEFINED ],

    # others
    "over": ['next', 1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "next": ['next', 1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "last": ['last', -1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "previous": ['previous', -1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "this": ['this', 0, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "in": ['in', 1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "ago": ['ago', 1, TokenType.OFFSET, TokenSubType.UNDEFINED ],
    "of": ['of', None, TokenType.DATE_INFIX, TokenSubType.UNDEFINED ],

    ",": [',', None, TokenType.LIST_DELIMITER, TokenSubType.UNDEFINED ],
    ";": [',', None, TokenType.LIST_DELIMITER, TokenSubType.UNDEFINED ],
    "-": ['-', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED ],
    "to": ['to', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED ],
    "and": ['and', None, TokenType.RANGE_INFIX, TokenSubType.UNDEFINED ],
    "between": ['between', None, TokenType.RANGE_PREFIX, TokenSubType.UNDEFINED ],

    "now": ['now', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED ],
    "tomorrow": ['tomorrow', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED ],
    "today": ['today', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED ],
    "yesterday": ['yesterday', None, TokenType.DATE_TIME_RANGE, TokenSubType.UNDEFINED],

}

ORDINAL_POSTFIXES = ['st', 'nd', 'rd', 'th']

CALENDER_KEYWORDS = [TokenType.WEEKDAY, TokenType.MONTH, TokenType.YEAR]

DATETIME_REFERENCE = [TokenType.DATE, TokenType.TIME, TokenType.DATE_TIME,
                      TokenType.WEEKDAY, TokenType.WEEK, TokenType.MONTH, TokenType.YEAR]

RE_TIME_FORMAT = re.compile(r"^([0-9]|[0-1][0-9]|2[0-3]):[0-5][0-9]?(:[0-5][0-9])?(?:[.,][0-9]+)?$")


class DateTimeTuple:
    def __init__(self, year=None, month=None, day=None,
                 hour=None, minute=None, second=None,
                 millisecond=None, microsecond=None):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.millisecond = millisecond
        self.microsecond = microsecond

    @property
    def has_year(self) -> bool:
        return self.year is not None

    @property
    def has_month(self) -> bool:
        return self.month is not None

    @property
    def has_day(self) -> bool:
        return self.day is not None

    @property
    def has_hour(self) -> bool:
        return self.hour is not None

    @property
    def has_minute(self) -> bool:
        return self.minute is not None

    @property
    def has_second(self) -> bool:
        return self.second is not None

    @property
    def has_millisecond(self) -> bool:
        return self.millisecond is not None

    @property
    def has_microsecond(self) -> bool:
        return self.microsecond is not None

    def to_datetime(self, ref_datetime: datetime = None):
        if ref_datetime is None:
            ref_datetime = datetime.now()
        year = self.year if self.has_year else ref_datetime.year
        month = self.month if self.has_month else ref_datetime.month
        day = self.day if self.has_day else ref_datetime.day
        hour = self.hour if self.has_hour else ref_datetime.hour
        minute = self.minute if self.has_minute else ref_datetime.minute
        second = self.second if self.has_second else ref_datetime.second
        microsecond = self.millisecond * 1000 if self.has_millisecond else ref_datetime.microsecond
        if self.has_microsecond:
            microsecond = self.microsecond if self.has_microsecond else ref_datetime.microsecond % 1000
        return datetime(year, month, day, hour, minute, second, microsecond)

    def __add__(self, other):
        if isinstance(other, DateTimeTuple):
            return DateTimeTuple(year=other.year if self.has_year else self.year,
                                 month=other.month if self.has_month else self.month,
                                 day=other.day if self.has_day else self.day,
                                 hour=other.hour if self.has_hour else self.hour,
                                 minute=other.minute if self.has_minute else self.minute,
                                 second=other.second if self.has_second else self.second,
                                 millisecond=other.millisecond if self.has_millisecond else self.millisecond,
                                 microsecond=other.microsecond if self.has_microsecond else self.microsecond
                                 )
        raise ValueError(f"Unsupported operand type(s) for +: '{type(self)}' and '{type(other)}'")

    def __str__(self):
        args = []
        if self.has_year:
            args.append(f"year={self.year}")
        if self.has_month:
            args.append(f"month={self.month}")
        if self.has_day:
            args.append(f"day={self.day}")
        if self.has_hour:
            args.append(f"hour={self.hour}")
        if self.has_minute:
            args.append(f"minute={self.minute}")
        if self.has_second:
            args.append(f"second={self.second}")
        if self.has_millisecond:
            args.append(f"millisecond={self.millisecond}")
        if self.has_microsecond:
            args.append(f"microsecond={self.microsecond}")
        return f"DateTimeTuple({', '.join(args)})"

    def __repr__(self):
        return self.__str__()


class Token:
    """Represents a token in a date text."""

    def __init__(self, text: str, token_type=TokenType.UNKNOWN, token_sub_type=TokenSubType.UNDEFINED, value=None, raw_text=None):
        self.type: TokenType = token_type
        self.sub_type: TokenSubType = token_sub_type
        self.text: str = text
        self.raw_text: str = raw_text if raw_text else text
        self.ordinal: int = 0
        self.value: Any = value
        self.priority: int = 0

    def __str__(self):
        return f"{'.' * (30 - len(self.type.name))}{self.type}.{self.sub_type}: '{self.text}' , value:={self.value}"

    def __repr__(self):
        return self.__str__()


class TokenList(list):
    """A navigable list of tokens."""

    def __init__(self, tokens: list[Token]):
        super().__init__(tokens)
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self):
            self.index += 1
            return self[self.index - 1]
        else:
            raise StopIteration

    def peek(self):
        if self.index < len(self):
            return self[self.index]
        else:
            return None

    def next(self):
        if self.index < len(self):
            self.index += 1
            return self[self.index - 1]
        else:
            return None

    def previous(self):
        if self.index > 0:
            self.index -= 1
            return self[self.index]
        else:
            return None

    def offset(self, offset: int):
        if -1 < self.index + offset < len(self):
            return self[self.index + offset]
        else:
            return None

    def remaining(self):
        return self[self.index:]

    def has_next(self):
        return self.index < len(self)

    def has_previous(self):
        return self.index > 0

    def reset(self):
        self.index = 0

    def __str__(self):
        return f"TokenList({super().__str__()})"

    def __repr__(self):
        return f"TokenList({super().__repr__()})"


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
            if text.endswith(","):
                stack.append(Token(",", token_type=TokenType.LIST_DELIMITER))
                text = text[:-1]

            # translate aliases and process date text keywords
            raw_text = text
            text = ALIASES.get(text, text)
            if text in KEYWORDS:
                text, value, token_type, sub_type = KEYWORDS[text]
                tokens.append(Token(text=text, token_type=token_type, token_sub_type=sub_type,  value=value, raw_text=raw_text))
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
                tokens.append(Token(text, TokenType.TIME, dateutil_parse(text, parser_info, fuzzy=True).time()))
                continue
            try:
                date = dateutil_parse(text, parser_info, fuzzy=True)
                if date.time() == time(0, 0, 0):
                    tokens.append(Token(text, TokenType.DATE, value=date))
                else:
                    tokens.append(Token(text, TokenType.DATE_TIME, value=date))
                continue

            except (ParserError, OverflowError):
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
