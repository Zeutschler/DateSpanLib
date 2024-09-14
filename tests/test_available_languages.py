from unittest import TestCase
from datetime import date, datetime

import numpy as np
import pandas as pd
from dateutil.parser import parse

from datespanlib import DateSpanSet, DateSpan, parse
from datespanlib.parser.tokenizer import Tokenizer, Token, TokenType

class TestAvailableLanguages(TestCase):

    def test_available_languages(self):
        dss = DateSpanSet()
        self.assertTrue("en" in dss.available_languages)
        self.assertFalse("klingon" in dss.available_languages)

