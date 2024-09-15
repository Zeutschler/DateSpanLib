# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license
from datetime import datetime, time
import sys
from unittest import TestCase

from datespanlib import DateSpan
from datespanlib.date_span_set import DateSpanSet
from datespanlib.parser.en.tokenizer import Tokenizer, Token, TokenType as TT, TokenSubType as TST, TokenList
from datespanlib.parser.en.parser import DateTextParser


class TestParserEn(TestCase):
    def setUp(self):
        self.debug = self.is_debug()

    @staticmethod
    def is_debug():
        """Check if the debugger is active. Used to print debug information."""
        gettrace = getattr(sys, 'gettrace', None)
        return (gettrace() is not None) if (gettrace is not None) else False


    def test_datespans(self):

        texts = [("1st of January 2024", DateSpan(datetime(2024, 1, 1)).full_day()),
                 ("1st day of January, February and March 2024", None),
                 ("last week", DateSpan.now().shift(days=-7).full_week()),
                 ("next 3 days",DateSpan.now().shift(days=1).full_day().shift_end(days=2)),
                 ("3rd week of 2024",None),
                 ("08.09.2024", DateSpan(datetime(2024, 9, 8)).full_day() ),
                 ("2024/09/08", DateSpan(datetime(2024, 9, 8)).full_day()),
                 ("2024-09-08", DateSpan(datetime(2024, 9, 8)).full_day()),
                 ("19:00", DateSpan.now().with_time(time(19, 0)).full_hour()),
                 ("1:34:45", DateSpan.now().with_time(time(1, 34, 45)).full_second() ),
                 ("1:34:45.123", DateSpan.now().with_time(time(1, 34, 45, 123))),
                 ("1:34:45.123456", DateSpan.now().with_time(time(1, 34, 45, 123456))),
                 ("2007-08-31T16:47+00:00", DateSpan(datetime(2007, 8, 31, 16, 47))),
                 ("2007-12-24T18:21Z", DateSpan(datetime(2007, 12, 24, 18, 21))),
                 ("2008-02-01T09:00:22+05", DateSpan(datetime(2008, 2, 1, 9, 0, 22))),
                 ("2009-01-01T12:00:00+01:00", DateSpan(datetime(2009, 1, 1, 12, 0), None)),
                 ("2010-01-01T12:00:00.001+02:00", DateSpan(datetime(2010, 1, 1, 12, 0, 0, 1000)))]

        for text, target in texts:
            try:
                dss = DateSpanSet(text)
                if target is not None:
                    self.assertEqual(dss[0], target)
                if self.debug:
                    print(f"\nTokens for '{text}':")
                    for pos, span in enumerate(dss):
                        print(f"{pos + 1:02d}: {span}")
            except Exception as e:
                if self.debug:
                    print(f"Error: {e}")
