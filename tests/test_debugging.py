# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from unittest import TestCase

from datespan.date_span import DateSpan


class TestDateTextParser(TestCase):
    def test_datespan_parsing(self):
        result = DateSpan('2023-01-01', '2023-01-31')
        self.assertEqual(DateSpan('January 2023'), result)
