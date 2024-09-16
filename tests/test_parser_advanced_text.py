# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license
from datetime import datetime, time
import sys
from unittest import TestCase

from datespanlib import DateSpan
from datespanlib.date_span_set import DateSpanSet


class TestParser(TestCase):
    def setUp(self):
        self.debug = self.is_debug()

    @staticmethod
    def is_debug():
        """Check if the debugger is active. Used to print debug information."""
        gettrace = getattr(sys, 'gettrace', None)
        return (gettrace() is not None) if (gettrace is not None) else False

    def test_advanced(self):
        samples = [
            "this week",
            "last week",
            "next 3 months",
            "Jan, Feb and August of 2024",
            "2024 YTD",
            "yesterday",
            "2024-09-13",
            "between June and August 2023",
            "past 2 weeks",
            "this month",
            "from 2024-09-01 to 2024-09-15",
            "last week; next 3 months; Jan, Feb and August of 2024; from 2024-09-01 to 2024-09-15",
            "august last year",
            "today",
            "yesterday",
            "last week",
            "this month",
            "next 2 months",
            "from 2024-09-01 to 2024-09-15",
            "Jan, Feb and August of 2024",
            "MTD",
            "QTD",
            "YTD",
            "from 2024-09-01 14:00 to 2024-09-15 15:00",
            "between 2024-09-10 08:30 and 2024-09-10 17:45",
            "2024-09-05 12:00 to 14:00",
            "from 2024-09-15T09:00 to 2024-09-15T18:00",

            "since August 2024",
            "since 2024-08-15",
            "since 15.08.2024 14:00",
            "since 2024-08-15 14:00:00.123456",

            "2024-09-10 14:00:00.123",  # Milliseconds
            "2024-09-10 14:00:00.123456",  # Microseconds
            "from 2024-09-10 14:00:00.123 to 2024-09-10 15:00:00.789",
            "10/09/2024 14:00:00.123456",

            "from 2024-09-01 to 2024-09-10",
            "between 09/01/2024 and 09/10/2024",
            "from 09.01.2024 to 09.10.2024",
            "between 2024-09-01 and 2024-09-10",

            "now",
            "every 1st Monday of YTD",
            "every 1st monday in YTD",
            "every Mon, Tue, Wed in this month",
            "every Mon, Tue, Wed of this month",
            "every Friday of next month",
            "every 2nd Friday of next month",
            "every Mon and Thu of this quarter",

            "every Mon, Wed, Fri of this month",
            "every 2nd Tuesday in next quarter",
            "every Friday of 2024", #todo: days not parsed in iterative expressions
            "every last Friday of the year", #todo: skip "the" tokens

            "today; yesterday; last week",
        ]

        for sample in samples:
            print(f"Text: {sample}")
            try:
                dss = DateSpanSet.parse(sample)
                for span in dss:
                    print(f"\t{span}")
            except Exception as e:
                print(f"\tError: {e}")
                #exit()
