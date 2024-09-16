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

    def test_parse_simple_datespans(self):

        # ("2024 qrt. to date", "2024 qtd", TST.QUARTER),
        # ("2024 quarter to date", "2024 qtd", TST.QUARTER),
        # ("2024 year to date", "2024 ytd", TST.YEAR),
        # ("2024 month to date", "2024 mtd", TST.MONTH),
        # ("2024 week to date", "2024 wtd", TST.WEEK),
        # ("10:23:45 pm.", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 pm", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 p.m.", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 a.m.", "10:23:45", TT.TIME, time(10, 23, 45))
        # ("10:23:45 pm.", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 pm", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 p.m.", "22:23:45", TT.TIME, time(22, 23, 45)),
        # ("10:23:45 a.m.", "10:23:45", TT.TIME, time(10, 23, 45)),

        texts = [
            # “Last 3 months”: Can be interpreted either as full calendar months or a rolling period, depending on context.
            # “Past 3 months”: Usually emphasizes a rolling 3-month window, typically starting from today’s date.
            # “Previous 3 months”: More commonly refers to the full 3 calendar months immediately before the current one.
            ("last 3 month", DateSpan.now().full_quarter()), # todo: ??? either 3 full month or rolling 3 month ???
            ("past 3 month", DateSpan.now().full_quarter()), # todo: ??? either 3 full month or rolling 3 month ???
            ("this quarter", DateSpan.now().full_quarter()),
            ("this minute", DateSpan.now().full_minute()),
            ("2024", DateSpan(datetime(2024, 1, 1)).full_year()),
            ("March", DateSpan(datetime(datetime.now().year, 3, 1)).full_month()),
            ("Jan 2024", DateSpan(datetime(2024, 1, 1)).full_month()),
            ("last month", DateSpan(datetime.now()).full_month().shift(months=-1)),
            ("previous month", DateSpan(datetime.now()).full_month().shift(months=-1)),
            ("prev. month", DateSpan(datetime.now()).full_month().shift(months=-1)),
            ("actual month", DateSpan(datetime.now()).full_month()),
            ("next month", DateSpan(datetime.now()).full_month().shift(months=1)),
            ("next year", DateSpan(datetime.now()).full_year().shift(years=1)),
            ("today", DateSpan(datetime.now()).full_day()),
            ("yesterday", DateSpan(datetime.now()).shift(days=-1).full_day()),
            ("ytd", DateSpan(datetime.now()).ytd()),
        ]

        for text, test in texts:
            dss = DateSpanSet(text)
            a = dss[0]
            if self.debug:
                print (f"Text: {text}")
                # for token in dss.
                #     print(f"\t{token}")
                # print(f"\tvalue := {a}")
                print (f"\t{a}")
            # self.assertTrue(a == test, f"Expected: {test}, got: {a} for text: '{text}'")

