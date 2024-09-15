# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license

from unittest import TestCase
from datespanlib.date_span_set import DateSpanSet


class TestAvailableLanguages(TestCase):

    def test_available_languages(self):
        dss = DateSpanSet()
        self.assertTrue("en" in dss.available_languages)
        self.assertFalse("klingon" in dss.available_languages)

