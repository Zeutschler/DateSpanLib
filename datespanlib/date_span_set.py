from __future__ import annotations

from typing import Any

import uuid
from datetime import datetime
from dateutil.parser import parserinfo

from datespanlib.parser.base_parser import DateTextLanguageParser
from datespanlib.date_span import DateSpan
import datespanlib.parser.loader as loader


class DateSpanSet:
    """
    Represents a sorted set of DateSpan objects. Overlapping DateSpan objects are automatically merged together.
    Provides methods to filter, merge, subtract and compare DateSpan objects as well as to convert them into
    SQL fragments or Python filter functions.
    """
    def __init__(self, definition: Any | None = None, language: str | None = "en", parser_info: parserinfo | None = None):
        """
        Initializes a new DateSpanSet based on a given set of date span set definition.
        The date span set definition can be a string, a DateSpan, datetime, date or time object or a list of these.

        Arguments:
            definition: (optional) a string, a DateSpan, datetime, date or time object or a list of these.

            language: (optional) An ISO 639-1 2-digit language code for the language of the text to parse.
                Default language is 'en' for English.

            parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                datespan_text. If not defined, the default parser of the dateutil library will be used.

        Errors:
            ValueError: If the language is not supported or the text cannot be parsed.
        """
        # super().__init__()
        self._spans: list[DateSpan] = []   # The internal list of date spans objects.
        self._definition: str | None = definition
        self._parser_info: parserinfo | None = parser_info

        # set and load language
        if not loader.language_parsers:
            loader.load_language_parsers()
        self._language: str | None = language.lower().strip() if isinstance(language, str) else "en"
        if self._language not in loader.language_parsers:
            raise ValueError(f"Date span text parsing for language '{language}' is not supported. "
                             f"The respective parser could not be loaded or instantiated.")
        self._parser: DateTextLanguageParser | None = loader.language_parsers[language]

        self._iter_index = 0
        if definition is not None:
            self._parse(definition, parser_info)

    # Magic Methods
    def __iter__(self):
        self._iter_index = -1
        return self

    def __next__(self):  # Python 2: def next(self)
        self._iter_index += 1
        if self._iter_index < len(self._spans):
            return self._spans[self._iter_index]
        raise StopIteration

    def __len__(self):
        return len(self._spans)

    def __getitem__(self, item):
        return self._spans[item]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}[{len(self._spans)}]('{self._definition}')"

    def __add__(self, other) -> DateSpanSet:
        return self.merge(other)

    def __sub__(self, other) -> DateSpanSet:
        return self.intersect(other)

    def __eq__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            if len(self._spans) != len(other._spans):
                return False
            for i, span in enumerate(self._spans):
                if span != other._spans[i]:
                    return False
            return True
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start < other.start
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start <= other.start
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start > other.start
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start >= other.start
        return False

    def __contains__(self, item) -> bool:
        if isinstance(item, DateSpan):
            for span in self._spans:
                if span == item:
                    return True
            return False
        elif isinstance(item, datetime):
            for span in self._spans:
                if span.contains(item):
                    return True
            return False
        return False

    def __bool__(self) -> bool:
        return len(self._spans) > 0

    def __hash__(self) -> int:
        return hash(tuple(self._spans))

    def __copy__(self) -> DateSpanSet:
        return self.clone()
    # endregion

    # region Public Properties and Methods
    @property
    def available_languages(self) -> list[str]:
        """ Returns a list of available languages for parsing date, time or date span texts."""
        return list(loader.language_parsers.keys())

    @property
    def language(self) -> str:
        """ Returns the ISO 639-1 language 2-difit code of the parser, e.g. 'en' for English."""
        return self._parser.language

    @property
    def start(self) -> datetime | None:
        """Returns the start date of the first DateSpan object in the set."""
        if len(self._spans) > 0:
            return self._spans[0].start
        return None

    @property
    def end(self) -> datetime | None:
        """ Returns the end date of the last DateSpan object in the set."""
        if len(self._spans) > 0:
            return self._spans[-1].end
        return None

    def clone(self) -> DateSpanSet:
        """ Returns a deep copy of the DateSpanSet object."""
        dss = DateSpanSet()
        dss._definition = self._definition
        dss._spans = [ds.clone() for ds in self._spans]
        dss._parser = self._parser
        dss._parser_info = self._parser_info
        return dss

    def add(self, other:DateSpanSet | DateSpan | str) -> None:
        """ Adds a new DateSpan object to the DateSpanSet."""
        return

    def remove(self, other:DateSpanSet | DateSpan | str) -> None:
        """ Removes a DateSpan object from the DateSpanSet."""
        raise NotImplementedError()

    def shift(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0,
              microseconds: int = 0, weeks: int = 0) -> DateSpan:
        """
        Shifts all contained date spans by the given +/- time delta.
        """
        if not self._spans:
            new_spans: list[DateSpan] = []
            for span in self._spans:
                new_spans.append(span.shift(years=years, months=months, days=days, hours=hours, minutes=minutes,
                           seconds=seconds, microseconds=microseconds, weeks=weeks))
            self._spans = new_spans
    # endregion


    # region Class Methods
    @classmethod
    def parse(cls, datespan_text: str, language: str | None = "en", parser_info: parserinfo | None = None) -> DateSpanSet:
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
                >>> DateSpanSet.parse('last month')  # if today would be in February 2024
                DateSpanSet([DateSpan(datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 31, 23, 59, 59, 999999))])
            """
        return cls(definition=datespan_text, language=language, parser_info=parser_info)

    @classmethod
    def try_parse(cls, datespan_text: str, language: str | None = "en", parser_info: parserinfo | None = None) -> DateSpanSet | None:
        """
            Creates a new DateSpanSet instance and parses the given text into a set of DateSpan objects. If
            the text cannot be parsed, None is returned.

            Arguments:
                datespan_text: The date span text to parse, e.g. 'last month', 'next 3 days', 'yesterday' or 'Jan 2024'.
                parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                    datespan_text. If not defined, the default parser of the dateutil library will be used.

            Returns:
                The DateSpanSet instance contain 0 to N DateSpan objects derived from the given text or None.

            Examples:
                >>> DateSpanSet.parse('last month')  # if today would be in February 2024
                DateSpanSet([DateSpan(datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 31, 23, 59, 59, 999999))])
            """
        try:
            dss = cls(definition=datespan_text, language=language, parser_info=parser_info)
            return dss
        except ValueError:
            return None
    # endregion

    
    # region Data Processing Methods And Callables
    def to_sql(self, column: str, line_breaks: bool = False, add_comment: bool = True, indentation_in_tabs:int = 0) -> str:
        """
        Converts the date spans representing the DateFilter into an ANSI-SQL compliant SQL fragment to be used
        for the execution of SQL queries.

        Arguments:
            column: The name of the SQL table column to filter.
            line_breaks: (optional) Flag if each date spans should be written in a separate line.
            add_comment: (optional) Flag if a comment with the date span text should be added to the SQL fragment.
                If line_breaks is True, the comment will be added as a separate line, otherwise as an inline comment.
            indentation_in_tabs: (optional) The number of tabs to use for indentation of an SQL fragment.
                Only used if line_breaks is True.

        Returns:
            A string containing an ANSI-SQL compliant fragment to be used in the WHERE clause of an SQL query.
        """
        filters: list[str] = []
        column = column.strip()
        if " " in column and not column[0] in "['\"":
            column = f"[{column}]"
        for i, span in enumerate(self._spans):
            filters.append(f"({column} BETWEEN '{span.start.isoformat()}' AND '{span.end.isoformat()}')")
        comment = f"{len(filters)} filters added from {self.__str__()}" if add_comment else ""
        inline_comment = f" /* {comment} */ " if add_comment else ""
        separate_comment = f"-- {comment}" if add_comment else ""
        if indentation_in_tabs > 0:
            indent = "\t" * indentation_in_tabs
            filters = [f"{indent}{f}" for f in filters]
            separate_comment = f"{indent}{separate_comment}"
        if line_breaks:
            if add_comment:
                return f"{separate_comment}\n" + "OR\n".join(filters)
            return "OR\n".join(filters)
        return " OR ".join(filters) + inline_comment


    def to_function(self, return_sourceCde: bool = False) -> callable | str:
        """
        Generate a compiled Python function that can be directly used as a filter function
        within Python, Pandas or other. The lambda function will return True if the input
        datetime is within the date spans of the DateFilter.

        Arguments:
            return_sourceCde: If True, the source code of the function will be returned as a string
                for code reuse. If False, the function will be returned as a callable Python function.

        Examples:
            >>> filter = DateSpanSet("today").to_function()
            >>> print(filter(datetime.now()))
            True

        """
        from types import FunctionType

        # prepare source
        func_name = f"filter_{str(uuid.uuid4()).lower().replace('-', '')}"
        filters: list[str] = [f"def {func_name}(x):", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            filters.append(f"\tif {start} <= x <= {end}:")
            filters.append(f"\t\treturn True")
        filters.append(f"\treturn False")

        source = f"\n".join(filters)
        if return_sourceCde:
            return source
        # compile
        f_code = compile(source, "<bool>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "func_name")
        return f_func

    def to_lambda(self, return_source_code: bool = False) -> callable:
        """
        Generate a Python lambda function that can be directly used as a filter function
        within Python, Pandas or other. The lambda function will return True if the input
        datetime is within the date spans of the DateFilter.

        Arguments:
            return_source_code: If True, the source code of the lambda function will be returned as a string
                for code reuse. If False, the lambda function will be returned as a callable Python function.

        Examples:
            >>> filter = DateSpanSet("today").to_lambda()
            >>> print(filter(datetime.now()))
            True

        """

        # prepare source
        filters: list[str] = [f"lambda x :", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            if i > 0:
                filters.append(" or ")
            filters.append(f"{start} <= x <= {end}")

        source = f" ".join(filters)
        if return_source_code:
            return source
        # compile
        f_func = eval(source)
        return f_func

    def to_df_lambda(self, return_source_code: bool = False) -> callable:
        """
        Generate a Python lambda function that can be directly applied to Pandas series (column) or
        to a 1d NumPy ndarray as a filter function. This allows the use of NumPy's internal vectorized functions.
        If applied to Pandas, the function will return a boolean Pandas series with the same length as the input series,
        if applied to a NumPy ndarray, the function will return a boolean array with the same length as the input array,
        where True indicates that the input datetime is within the date spans of the DateFilter.

        Arguments:
            return_source_code: If True, the source code of the Numpy lambda function will be returned as a string
                for code reuse. If False, the lambda function will be returned as a callable Python function.

        Examples:
            >>> data = np.array([datetime.now(), datetime.now()])
            >>> filter = DateSpanSet("today").to_df_lambda()
            >>> print(filter(data))
            [True, True]
        """
        # prepare source
        filters: list[str] = [f"lambda x :", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            if i > 0:
                filters.append(" | ")
            filters.append(f"((x >= {start}) & (x <= {end}))")

        source = f" ".join(filters)
        if return_source_code:
            return source
        # compile
        f_func = eval(source)
        return f_func

    def to_tuples(self) -> list[tuple[datetime, datetime]]:
        """ Returns a list of tuples with start and end dates of all DateSpan objects in the DateSpanSet."""
        return [(ds.start, ds.end) for ds in self._spans]

    def filter(self, data: Any, return_mask:bool = False, return_index:bool=False) -> Any:
        """
        Filters the given data object, e.g. a Pandas DataFrame or Series, based on the date spans of the DateSpanSet.

        Arguments:
            data: The data object to filter, e.g. a Pandas DataFrame or Series.
            return_mask: (optional) If True, a boolean mask will be returned instead of the filtered data.
            return_index: (optional) If True, the index of the filtered data will be returned.

        Returns:
            A filter for the data object, e.g. a boolean Numpy ndarray for direct filtering of Pandas DataFrame or Series.

        Sample:
            >>> df = pd.DataFrame.from_dict({
            ...     "product": ["A", "B", "C", "A", "B", "C"],
            ...     "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
            ...              datetime(2024, 7, 1), datetime(2024, 7, 2),
            ...              datetime(2024, 12, 1), datetime(2023, 12, 2)],
            ...     "sales": [100, 150, 300, 200, 250, 350]
            ... })
            >>> spans = DateSpanSet("June and December 2024")
            >>> filtered_df = spans.filter(df["date"], return_mask=True)
            >>> print(filtered_df)

        """
        class_name = f"{data.__class__.__module__}.{data.__class__.__qualname__}"
        match class_name:
            case "pandas.core.frame.DataFrame":
                return self.to_df_lambda(data)
            case "pandas.core.series.Series":
                return self.to_df_lambda()(data)

        return data
    # endregion



    # region Set Operations
    def merge(self, other:DateSpanSet | DateSpan | str) -> DateSpanSet:
        """
        Merges the current DateSpanSet with another DateSpanSet, DateSpan or a string representing a data span.
        The resulting DateSpanSet will contain date spans representing all data spans of the current and the other
        DateSpanSet.

        Arguments:
            other: The other DateSpanSet, DateSpan or string to merge with the current DateSpanSet.

        Returns:
            A new DateSpanSet instance containing the merged date spans.
        """
        raise NotImplementedError()
        if isinstance(other, DateSpan | DateSpanSet | str):
            return DateSpanSet([self, other])
        return self.clone()

    def intersect(self, other:DateSpanSet | DateSpan | str) -> DateSpanSet:
        """
        Intersects the current DateSpanSet with another DateSpanSet, DateSpan or a string representing a data span.
        The resulting DateSpanSet will contain data spans that represent the current DataSpanSet minus the date spans
        that are not contained in the other DateSpanSet.

        Arguments:
            other: The other DateSpanSet, DateSpan or string to merge with the current DateSpanSet.

        Returns:
            A new DateSpanSet instance containing the intersected data spans.
        """
        raise NotImplementedError()

    # end region



    # region Internal Methods
    def _parse(self, text: str, parser_info: parserinfo | None = None) -> bool:
        """
        Parses the given text into a set of DateSpan objects.
        """
        self._message = None
        self._spans.clear()
        try:
            ds: DateSpan | list[DateSpan] = self._parser.parse(text, parser_info)
            if isinstance(ds, DateSpan):
                self._spans.append(ds)
            else:
                self._spans.extend(ds)
        except ValueError as e:
            raise e
        return True
    # endregion
