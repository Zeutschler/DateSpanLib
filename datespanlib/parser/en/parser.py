# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license
from datetime import datetime

from dateutil.parser import parse as dateutil_parse, parserinfo
from dateutil.parser import ParserError

from datespanlib.date_span import DateSpan
import datespanlib.date_methods as dtm
from datespanlib.parser.base_parser import DateTextLanguageParser
from datespanlib.parser.en.tokenizer import Tokenizer, Token, TokenList
from datespanlib.parser.en.tokenizer import TokenType as TT
from datespanlib.parser.en.tokenizer import TokenSubType as TST

KEYWORD_RESOLVERS = {"now": dtm.now, "tomorrow": dtm.tomorrow, "today": dtm.today, "yesterday": dtm.yesterday,
                     "ytd": dtm.actual_ytd, "mtd": dtm.actual_mtd, "qtd": dtm.actual_qtd, "wtd": dtm.actual_wtd,
                     "month": dtm.actual_month, "week": dtm.actual_week, "quarter": dtm.actual_quarter,
                     "year": dtm.actual_year,
                     "monday": dtm.monday, "tuesday": dtm.tuesday, "wednesday": dtm.wednesday, "thursday": dtm.thursday,
                     "friday": dtm.friday, "saturday": dtm.saturday, "sunday": dtm.sunday,
                     "january": dtm.january, "february": dtm.february, "march": dtm.march, "april": dtm.april,
                     "may": dtm.may, "june": dtm.june, "july": dtm.july, "august": dtm.august,
                     "september": dtm.september, "october": dtm.october, "november": dtm.november,
                     "december": dtm.december,
                     }


class ExpressionContext:
    def __init__(self):
        self.text: str | None = None

        self.datespan: DateSpan | None = None
        self.second: int | None = None
        self.minute: int | None = None
        self.hour: int | None = None

        self.day: int | None = None
        self.month: int | None = None
        self.quarter: int | None = None
        self.year: int | None = None

        self.date: datetime | None = None
        self.time: datetime | None = None
        self.datetime: datetime | None = None

        self.offset: int | None = None

    def clone(self):
        ec = ExpressionContext()
        ec.text = self.text
        ec.datespan = self.datespan
        ec.second = self.second
        ec.minute = self.minute
        ec.hour = self.hour
        ec.day = self.day
        ec.month = self.month
        ec.quarter = self.quarter
        ec.year = self.year
        ec.date = self.date
        ec.time = self.time
        ec.datetime = self.datetime
        ec.offset = self.offset
        return ec

    @property
    def value(self) -> DateSpan:
        # it's already a datespan, return it
        if self.datespan is not None:
            return self.datespan

        # a specific datetime with date and time was given, return it
        if self.datetime is not None:
            return DateSpan(self.datetime, self.datetime)

        # some evaluation is required, lets start with today
        ds = DateSpan()
        if self.date is not None:
            ds = DateSpan(self.date).full_day()
        if self.time is not None:
            ds = ds.with_time(self.time)

        if self.year is not None:
            if self.quarter is not None:
                if self.month is not None:
                    return DateSpan(message=f"Subsequent quarter and month in date expression "
                                            f"'{self.text}' are not supported. "
                                            f"You maybe miss a ',', 'to' or 'and' in between.")
                ds = DateSpan(datetime(self.year, self.quarter * 3 - 2, 1)).full_quarter()
            elif self.month is not None:
                if self.day is not None:
                    ds = DateSpan(datetime(self.year, self.month, self.day))
                else:
                    ds = DateSpan(datetime(self.year, self.month, 1)).full_month()
            else:
                ds = DateSpan(datetime(self.year, 1, 1)).full_year()
        else:
            ds = DateSpan.now().full_day()

        if self.second is not None:
            ds = ds.full_second()
        elif self.minute is not None:
            return ds.full_minute()
        elif self.hour is not None:
            return ds.full_hour()

        return ds


class DateTextParser(DateTextLanguageParser):
    """
    English language DateText parser. Converts date- and time-related text
    in English language into a (`datetime`, `datetime`) time-span tuples.
    """
    LANGUAGE: str = "en"

    def __init__(self):
        self._message: str | None = None
        self._text: str | None = None
        self._is_parsed: bool = False
        self._is_evaluated: bool = False

        self.tokens: TokenList = TokenList()
        self.expressions: list[TokenList] = []
        self._spans: list[DateSpan] = []

    @property
    def language(self) -> str:
        return self.LANGUAGE

    @property
    def message(self) -> str:
        return self._message

    @property
    def text(self) -> str:
        return self._text

    def __str__(self):
        return f"DateTextParser('{self._text}', lang={self.language})"

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.expressions)

    def __getitem__(self, item):
        return self.expressions[item]

    def __iter__(self):
        for expression in self.expressions:
            yield expression

    def evaluate(self, text: str, parser_info: parserinfo | None = None) -> DateSpan | list[DateSpan]:
        """
        Evaluates a date text string to a list of DateSpans, each containing a (`datetime`, `datetime`) time-span tuples.

        Arguments:
            text: The date text string to parsed and evaluated.
            parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                datespan_text. If not defined, the default parser of the dateutil library will be used.

        Returns:
            A list of DateSpan objects or None. If None is returned, the text could not be parsed.
        """

        # reset the parser
        self._is_parsed = False
        self._is_evaluated = False
        self._message = None
        self._text = text
        self.expressions = []
        self._spans: list[DateSpan] = []

        # 1. Tokenize the text
        self.tokens = Tokenizer().tokenize(text, parser_info)
        if len(self.tokens) == 0:
            # todo: should better we return now() ?
            raise ValueError("Empty date text string.")

        # 2. split subexpressions, delimited by ";"
        self.split_expressions()  # from here on, we work with self.expressions, no longer with the full token list

        # 3. Reduce tokens, if possible
        self._reduce()

        # 4. build token tree for evaluation
        self._parse()

        # 5. evaluate the tokens
        if self._is_parsed:
            self._evaluate()
        if self._is_evaluated:
            return self._spans
        raise ValueError(f"Failed to parse date text '{text}'. {self._message}")


    def _parse(self, parser_info: parserinfo | None = None):
        """ Parses a list of tokens into a (`datetime`, `datetime`) time-span tuple."""

        for exp in self.expressions:
            if len(exp) == 1: # 1-token date text, e.g. "today", "yesterday" can be skipped. They are already parsed
                continue

            # todo: missing implementation to build token tree

        self._is_parsed = True

    def _evaluate(self, parser_info: parserinfo | None = None):
        self._is_evaluated = False
        self._spans = []

        for exp in self.expressions:
            # special case: just a single token expression
            if len(exp) == 1:
                ds = self.single_token_expression(exp[0])
                if not ds.is_undefined:
                    self._spans.append(ds)
                    continue

            success, spans = self._evaluate_expression(exp)
            if success:
                self._spans.extend(spans)
                continue

            # special case: two tokens, e.g. "2024 year"

            # The last resort: If we failed, the dateutil library may solve it...
            # For details please visit: https://dateutil.readthedocs.io/en/stable/index.html
            # Note: Dateutil does not return tuples for single dates, and has different
            #       behavior for some date texts. e.g. if its Tuesday, then `Monday` refers
            #       to the next Monday, but we want it to be the monday of this week.
            text = exp.to_text()
            try:
                result = dateutil_parse(text, fuzzy=True)
                return DateSpan(result)
            except (ParserError, OverflowError) as e:
                return DateSpan()

        self._is_evaluated = True

    def single_token_expression(self, token: Token) -> DateSpan:
        """ Evaluates a single token expression. """
        if token.type == TT.DATE:
            return DateSpan(token.value).full_day()
        elif token.type == TT.TIME:
            return DateSpan.now().with_time(token.value, token.text)
        if token.text in KEYWORD_RESOLVERS:
            return KEYWORD_RESOLVERS[token.text]()
        return DateSpan.undefined()

    def _evaluate_expression(self, exp: TokenList) -> tuple[bool, list[DateSpan]]:
        """ Evaluates a list of tokens into a list of (`datetime`, `datetime`) time-span tuples. """
        spans = []

        ec = ExpressionContext()
        ec.text = exp.to_text()
        for token in exp:
            if token.type == TT.DATE:
                ec.date = token.value
            elif token.type == TT.TIME:
                ec.time = token.value
            elif token.type == TT.DATE_TIME:
                ec.datetime = token.value
            elif token.type == TT.YEAR:
                ec.year = token.value
            elif token.type == TT.MONTH:
                ec.month = token.value

            elif token.type == TT.PERIOD_TO_DATE:
                if token.sub_type == TST.YEAR:
                    ec.year = token.value
                elif token.sub_type == TST.MONTH:
                    ec.month = token.value
                elif token.sub_type == TST.WEEK:
                    ec.week = token.value
                elif token.sub_type == TST.QUARTER:
                    if token.value is not None:
                        ec.quarter = token.value
                    if ec.quarter is None:
                        ec.datespan = DateSpan.today().qtd()
                else:
                    self._message = f"Token '{token.text}' is not yet supported."
                    return False, []

            elif token.type == TT.OFFSET:
                ec.offset = token.value

            elif token.type == TT.POSTFIX:
                # Dates
                if token.sub_type == TST.MONTH:
                    ec.datespan = DateSpan.today().full_month()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(months=ec.offset)
                elif token.sub_type == TST.DAY:
                    ec.datespan = DateSpan.today().full_day()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(days=ec.offset)
                elif token.sub_type == TST.WEEK:
                    ec.datespan = DateSpan.today().full_week()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(weeks=ec.offset)
                elif token.sub_type == TST.QUARTER:
                    ec.datespan = DateSpan.today().full_quarter()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(months=ec.offset * 3)
                elif token.sub_type == TST.YEAR:
                    ec.datespan = DateSpan.today().full_year()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(years=ec.offset)
                #times
                elif token.sub_type == TST.HOUR:
                    ec.datespan = DateSpan.today().full_hour()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(hours=ec.offset)
                elif token.sub_type == TST.MINUTE:
                    ec.datespan = DateSpan.today().full_minute()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(minutes=ec.offset)
                elif token.sub_type == TST.SECOND:
                    ec.datespan = DateSpan.today().full_second()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(seconds=ec.offset)
                elif token.sub_type == TST.MILLISECOND:
                    ec.datespan = DateSpan.today().full_millisecond()
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(microseconds=ec.offset * 1000)
                elif token.sub_type == TST.MICROSECOND:
                    ec.datespan = DateSpan(datetime.now())
                    if ec.offset is not None:
                        ec.datespan = ec.datespan.shift(microseconds=ec.offset)

            elif token.type == TT.DATE_TIME_RANGE:
                if token.sub_type == TST.YEAR:
                    ec.datespan = DateSpan(datetime(token.value, 1, 1)).full_year()
                    ec.year = token.value
                elif token.sub_type == TST.MONTH:
                    ec.datespan = DateSpan(datetime(token.value, 1, 1)).full_month()
                    ec.month = token.value
                # elif token.sub_type == TST.WEEK:
                #     pass #ec.datespan = DateSpan.full_week()
                # elif token.sub_type == TST.QUARTER:
                #     ec.datespan = DateSpan(datetime(token.value, 1, 1)).full_month()
                #     ec.quarter = token.value
                else:
                    self._message = f"Token type {token.type} = '{token.text}' is not yet supported."
                    return False, []

            else:
                self._message = f"Token type {token.type} = '{token.text}' is not yet supported."
                return False, []

        span = ec.value
        spans.append(span)

        return True, spans



    def split_expressions(self):
        """ Splits the list of tokens into subexpressions, delimited by ";". """
        tokens = self.tokens
        start = 0
        for i, token in enumerate(tokens):
            if token.type == TT.STOP:
                self.expressions.append(tokens[start:i])
                start = i + 1
        self.expressions.append(tokens[start:])

    def _reduce(self):
        """ Reduces the list of tokens per expression by combining those tokens that can be combined, e.g. "year to date" -> "ytd". """
        for tokens in self.expressions:
            self.reduce_period_to_date(tokens)
            self.reduce_am_pm_postfix(tokens)

    def reduce_period_to_date(self, tokens: TokenList):
        # Reduce ["year", "to", "date"] -> "ytd" for years, months, weeks, quarters
        success, index, token = tokens.find_first(type=TT.POSTFIX)  # find "month", "week "quarter", "year"
        while success:
            if index + 2 < len(tokens):  # enough tokens left for "... to date"
                if tokens[index + 1].text == "to" and tokens[index + 2].text == "date":
                    token = tokens[index]
                    if token.sub_type in [TST.YEAR, TST.MONTH, TST.WEEK, TST.QUARTER]:
                        # reduce the tokens and set up the new token
                        tokens.pop(index=index + 1, count=2)
                        tokens[index] = Token(text=f"{token.text[0]}td", value=token.value,
                                              token_type=TT.PERIOD_TO_DATE, token_sub_type=token.sub_type)
            else:
                return
            success, index, token = tokens.find_first(type=TT.POSTFIX, start=index + 1)

    def reduce_am_pm_postfix(self, tokens: TokenList):
        # Reduce ["10:34:12", "a.m."] -> "10:34:12" and ["10:34:12", "pm"] -> "22:34:12".
        success, index, token = tokens.find_first(type=(TT.TIME, TT.DATE_TIME))  # find "month", "week "quarter", "year"
        while success:
            if index + 1 < len(tokens):  # enough tokens left ?
                if tokens[index + 1].type == TT.TIME_POSTFIX:
                    token = tokens[index]
                    next_token = tokens[index + 1]
                    if next_token.text == "pm" and token.value.hour < 12:
                        token.value = token.value.replace(hour=token.value.hour + 12)
                    if next_token.text in ["am", "pm"]:
                        token.text = token.text + f" {next_token.text}"
                    tokens[index] = token
                    # reduce the tokens and set up the new token
                    tokens.pop(index=index + 1)

            else:
                return
            success, index, token = tokens.find_first(type=(TT.TIME, TT.DATE_TIME), start=index + 1)

# endregion
