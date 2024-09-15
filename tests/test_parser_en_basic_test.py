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

    def test_reduce_period_to_date(self):
        dtp1 = DateTextParser()
        dtp2 = DateTextParser()

        texts = [
            ("2024 qrt. to date", "2024 qtd", TST.QUARTER),
            ("2024 quarter to date", "2024 qtd", TST.QUARTER),
            ("2024 year to date","2024 ytd", TST.YEAR),
            ("2024 month to date", "2024 mtd", TST.MONTH),
            ("2024 week to date", "2024 wtd", TST.WEEK),
        ]
        for a,b, tst in texts:
            dtp1.evaluate(a)
            dtp2.evaluate(b)
            if self.debug:
                print (f"Text: {a}")
                for token in dtp1.tokens:
                    print(f"\t{token}")
            self.assertTrue(dtp1.tokens[0].type == TT.YEAR)
            self.assertTrue(dtp1.expressions[0][1].type == TT.PERIOD_TO_DATE and dtp1.expressions[0][1].sub_type == tst)
            self.assertTrue(dtp1.expressions[0] == dtp2.expressions[0])

    def test_reduce_am_pm(self):
        dtp1 = DateTextParser()
        dtp2 = DateTextParser()

        texts = [
            ("10:23:45 pm.", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 pm", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 p.m.", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 a.m.", "10:23:45", TT.TIME, time(10, 23, 45))
        ]
        for a, b, tt, test_value in texts:
            dtp1.evaluate(a)
            dtp2.evaluate(b)
            if self.debug:
                print (f"Text: {a}")
                for token in dtp1.tokens:
                    print(f"\t{token}")
            self.assertTrue(dtp1.expressions[0] == dtp2.expressions[0])
            self.assertTrue(dtp1.tokens[0].type == tt)
            self.assertTrue(dtp1.tokens[0].value == dtp2.tokens[0].value)
            self.assertTrue(dtp1.tokens[0].value == test_value)


    def test_reduce_list(self):
        dtp1 = DateTextParser()
        dtp2 = DateTextParser()

        texts = [
            ("10:23:45 pm.", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 pm", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 p.m.", "22:23:45", TT.TIME, time(22, 23, 45)),
            ("10:23:45 a.m.", "10:23:45", TT.TIME, time(10, 23, 45)),
        ]
        for a, b, tt, test_value in texts:
            dtp1.evaluate(a)
            dtp2.evaluate(b)
            if self.debug:
                print (f"Text: {a}")
                for token in dtp1.tokens:
                    print(f"\t{token}")
            self.assertTrue(dtp1.expressions[0] == dtp2.expressions[0])
            self.assertTrue(dtp1.tokens[0].type == tt)
            self.assertTrue(dtp1.tokens[0].value == dtp2.tokens[0].value)
            self.assertTrue(dtp1.tokens[0].value == test_value)


    def test_split_expressions(self):
        dtp = DateTextParser()
        dtp.evaluate("2024 qrt. to date; 2024 year to date")
        self.assertTrue(len(dtp.expressions) == 2)
        self.assertTrue(dtp.expressions[0][0].text == "2024")
        self.assertTrue(dtp.expressions[1][0].text == "2024")
        self.assertTrue(dtp.expressions[0][1].type == TT.PERIOD_TO_DATE and dtp.expressions[0][1].sub_type == TST.QUARTER)
        self.assertTrue(dtp.expressions[1][1].type == TT.PERIOD_TO_DATE and dtp.expressions[1][1].sub_type == TST.YEAR)


    def test_parse_simple_datespans(self):

        dtp = DateTextParser()
        texts = [
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

        for a, b in texts:
            ds_a = dtp.evaluate(a)[0]
            if self.debug:
                print (f"Text: {a}")
                for token in dtp.expressions[0]:
                    print(f"\t{token}")
                print(f"\tvalue := {ds_a}")
            self.assertTrue(ds_a == b)
