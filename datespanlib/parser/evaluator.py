import re
from datetime import datetime, time, timedelta

import dateutil.parser
from PIL.TiffTags import lookup
from dateutil.relativedelta import relativedelta

import datespanlib.date_methods as dtm
from parser.errors import EvaluationError, ParsingError
from parser.lexer import Token, TokenType, Lexer
from parser.parser import Parser


class Evaluator:
    """
    The Evaluator class takes the AST produced by the parser_old and computes the actual date spans.
    It handles the logic of converting relative dates and special keywords into concrete date ranges.
    """
    def __init__(self, statements):
        self.statements = statements  # List of statements (AST nodes)
        self.today = datetime.today()  # Current date and time
        self.evaluated_spans = []  # Store evaluated date spans

    def evaluate(self):
        """
        Evaluates all statements and returns a list of date spans for each statement.
        """
        try:
            all_date_spans = []
            for statement in self.statements:
                date_spans = []
                for node in statement:
                    spans = self.evaluate_node(node)
                    date_spans.extend(spans)
                all_date_spans.append(date_spans)
            self.evaluated_spans = all_date_spans
            return all_date_spans
        except Exception as e:
            # Raise an EvaluationError with details
            raise EvaluationError(str(e))

    def evaluate_node(self, node):
        """
        Evaluates a single AST node and returns the corresponding date spans.
        """
        node_type = node.value['type']
        if node_type == 'specific_date':
            return self.evaluate_specific_date(node.value['date'])
        elif node_type == 'relative':
            return self.evaluate_relative(node.value['tokens'])
        elif node_type == 'special':
            return self.evaluate_special(node.value['value'])
        elif node_type == 'months':
            return self.evaluate_months(node.value['tokens'])
        elif node_type == 'days':
            return self.evaluate_days(node.value['tokens'])

        elif node_type == 'range':
            return self.evaluate_range(node.value['start_tokens'], node.value['end_tokens'])
        elif node_type == 'since':
            return self.evaluate_since(node.value['tokens'])
        elif node_type == 'iterative':
            return self.evaluate_iterative(node.value['tokens'], node.value['period_tokens'])
        else:
            return []

    def evaluate_specific_date(self, date_str):
        """
        Evaluates a specific date string and returns the corresponding date span.
        """
        try:
            try:
                date = dateutil.parser.parse(date_str)
            except ValueError:
                # Parse the date string, allowing fuzzy parsing for complex formats
                date = dateutil.parser.parse(date_str, fuzzy=True, fuzzy_with_tokens=False)
        except ValueError:
            raise EvaluationError(f'Invalid date format: {date_str}')
        start = date
        end = date
        if date.time() == time(0, 0):
            # If time is not specified, set the span to cover the entire day
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
        return [(start, end)]

    def evaluate_range(self, start_tokens, end_tokens):
        """
        Evaluates a date range specified by start and end tokens.
        """
        # Evaluate the start date expression
        start_parser = Parser(start_tokens + [Token(TokenType.EOF)])
        try:
            start_ast_nodes = start_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse start date in range: {e}')
        if not start_ast_nodes:
            raise EvaluationError('Failed to parse start date in range')
        try:
            start_spans = self.evaluate_node(start_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate start date in range: {e}')
        if not start_spans:
            raise EvaluationError('Failed to evaluate start date in range')
        start_date = start_spans[0][0]

        # Evaluate the end date expression
        end_parser = Parser(end_tokens + [Token(TokenType.EOF)])
        try:
            end_ast_nodes = end_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse end date in range: {e}')
        if not end_ast_nodes:
            raise EvaluationError('Failed to parse end date in range')
        try:
            end_spans = self.evaluate_node(end_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate end date in range: {e}')
        if not end_spans:
            raise EvaluationError('Failed to evaluate end date in range')
        end_date = end_spans[0][1]

        # Handle case where only time is specified in end date
        if isinstance(end_date, time):
            end_date = datetime.combine(start_date.date(), end_date)

        return [(start_date, end_date)]

    def evaluate_since(self, tokens):
        """
        Evaluates a 'since' expression, calculating the date range from the specified date/time until now.
        """
        # Parse the date/time expression following 'since'
        parser = Parser(tokens + [Token(TokenType.EOF)])
        try:
            ast_nodes = parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse date in "since" expression: {e}')
        if not ast_nodes:
            raise EvaluationError('Failed to parse date in "since" expression')
        try:
            spans = self.evaluate_node(ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate date in "since" expression: {e}')
        if not spans:
            raise EvaluationError('Failed to evaluate date in "since" expression')
        start_date = spans[0][0]
        end_date = self.today
        return [(start_date, end_date)]

    def evaluate_iterative(self, tokens, period_tokens):
        """
        Evaluates an iterative date expression and returns the corresponding date spans.
        """
        # Parse the period expression
        period_parser = Parser(period_tokens + [Token(TokenType.EOF)])
        try:
            period_ast_nodes = period_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse period in iterative expression: {e}')
        if not period_ast_nodes:
            raise EvaluationError('Failed to parse period in iterative expression')
        try:
            period_spans = self.evaluate_node(period_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate period in iterative expression: {e}')
        if not period_spans:
            raise EvaluationError('Failed to evaluate period in iterative expression')
        period_start = period_spans[0][0]
        period_end = period_spans[0][1]

        # Determine days of the week
        idx = 0
        ordinals = []
        weekdays = []
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.ORDINAL:
                ord_value = self.ordinal_to_int(token.value)
                ordinals.append(ord_value)
            elif token.type == TokenType.IDENTIFIER and token.value in Lexer.DAY_ALIASES.values():
                weekday_num = self.weekday_name_to_num(token.value)
                weekdays.append(weekday_num)
            idx += 1

        if not weekdays:
            raise EvaluationError('No weekdays specified in iterative expression')

        # Generate dates
        date_spans = []
        current_date = period_start
        while current_date <= period_end:
            if current_date.weekday() in weekdays:
                if ordinals:
                    # Check if current date is the nth occurrence in the month
                    for ord_value in ordinals:
                        if self.is_nth_weekday_of_month(current_date, ord_value):
                            start = datetime.combine(current_date.date(), time.min)
                            end = datetime.combine(current_date.date(), time.max)
                            date_spans.append((start, end))
                else:
                    # No ordinal specified, include all matching weekdays
                    start = datetime.combine(current_date.date(), time.min)
                    end = datetime.combine(current_date.date(), time.max)
                    date_spans.append((start, end))
            current_date += timedelta(days=1)
        return date_spans

    def ordinal_to_int(self, ordinal_str):
        """
        Converts an ordinal string like '1st' to an integer.
        """
        return int(re.match(r'(\d+)(?:st|nd|rd|th)', ordinal_str).group(1))

    def weekday_name_to_num(self, weekday_name):
        """
        Converts a weekday name to its corresponding number (Monday=0, Sunday=6).
        """
        weekdays = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }
        return weekdays[weekday_name]

    def is_nth_weekday_of_month(self, date, n):
        """
        Checks if a date is the nth occurrence of its weekday in the month.
        """
        first_day = date.replace(day=1)
        weekday = date.weekday()
        count = 0
        while first_day <= date:
            if first_day.weekday() == weekday:
                count += 1
            if first_day == date:
                return count == n
            first_day += timedelta(days=1)
        return False

    def evaluate_relative(self, tokens):
        """
        Evaluates a relative date expression and returns the corresponding date span.
        """
        idx = 0
        direction = None  # 'last', 'next', 'this', or 'rolling'
        number = 1  # Default number if not specified
        unit = 'day'  # Default unit
        ordinal = None
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in ['last', 'past']:
                direction = 'last'
            elif token.type == TokenType.IDENTIFIER and token.value == 'next':
                direction = 'next'
            elif token.type == TokenType.IDENTIFIER and token.value == 'this':
                direction = 'this'
            elif token.type == TokenType.NUMBER:
                number = token.value
            elif token.type == TokenType.ORDINAL:
                ordinal = self.ordinal_to_int(token.value)
            elif token.type == TokenType.TIME_UNIT:
                unit = token.value
            elif token.type == TokenType.SPECIAL:
                # Handle rolling periods like 'R3M'
                if token.value.startswith('r') and token.value[-1] in ['d', 'w', 'm', 'y']:
                    direction = 'rolling'
                    number = int(token.value[1:-1])
                    unit_char = token.value[-1]
                    unit_map = {'d': 'day', 'w': 'week', 'm': 'month', 'y': 'year'}
                    unit = unit_map[unit_char]
                else:
                    return self.evaluate_special(token.value)
            idx += 1
        if direction == 'last':
            return self.calculate_past(number, unit)
        elif direction == 'next':
            return self.calculate_future(number, unit)
        elif direction == 'this':
            return self.calculate_this(unit)
        elif ordinal is not None:
            # Handle expressions like '1st Monday'
            return self.calculate_nth_weekday_in_period(ordinal, unit)
        elif direction == 'rolling':
            return self.calculate_past(number, unit)
        else:
            return []

    def evaluate_special(self, value):
        """
        Evaluates a special date expression and returns the corresponding date span.
        """
        if value == 'yesterday':
            date = self.today - timedelta(days=1)
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
            return [(start, end)]
        elif value == 'today':
            date = self.today
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
            return [(start, end)]
        elif value == 'tomorrow':
            date = self.today + timedelta(days=1)
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
            return [(start, end)]
        elif value == 'now':
            # Return the exact current time
            now = datetime.now()
            return [(now, now)]
        elif value == 'ytd':
            # Year-to-date: from the beginning of the year to today
            from_date = datetime(self.today.year, 1, 1)
            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(self.today.date(), time.max)
            return [(start, end)]
        elif value == 'qtd':
            # Quarter-to-date: from the beginning of the quarter to today
            quarter = (self.today.month - 1) // 3 + 1
            from_month = 3 * (quarter - 1) + 1
            from_date = datetime(self.today.year, from_month, 1)
            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(self.today.date(), time.max)
            return [(start, end)]
        elif value == 'mtd':
            # Month-to-date: from the beginning of the month to today
            from_date = datetime(self.today.year, self.today.month, 1)
            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(self.today.date(), time.max)
            return [(start, end)]
        elif value == 'wtd':
            # week-to-date: from the beginning of the month to today
            start = dtm.actual_week().start
            end = datetime.combine(self.today.date(), time.max)
            return [(start, end)]

        elif value in ['q1', 'q2', 'q3', 'q4']:
            # Specific quarter
            year = self.today.year
            quarter = int(value[1])
            from_month = 3 * (quarter - 1) + 1
            from_date = datetime(year, from_month, 1)
            to_date = from_date + relativedelta(months=3, days=-1)
            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(to_date.date(), time.max)
            return [(start, end)]
        elif value.startswith('r') and value[-1] in ['d', 'w', 'm', 'y'] and value[1:-1].isdigit():
            # Rolling periods like 'R3M' (last 3 months)
            number = int(value[1:-1])
            unit_char = value[-1]
            unit_map = {'d': 'day', 'w': 'week', 'm': 'month', 'y': 'year'}
            unit = unit_map[unit_char]
            return self.calculate_past(number, unit)
        else:
            return []

    def evaluate_months(self, tokens):
        """
        Evaluates a list of months, possibly with a year, and returns the corresponding date spans.
        """
        months = []
        year = self.today.year  # Default to current year
        idx = 0
        # Check if the last token is a number (year)
        if tokens and tokens[-1].type == TokenType.NUMBER:
            year = tokens[-1].value
            tokens = tokens[:-1]  # Remove the year from tokens
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in Lexer.MONTH_ALIASES.values():
                month_full_name = token.value
                months.append(month_full_name)
            idx += 1
        date_spans = []
        for month_name in months:
            # Get the month number from the month name
            month_number = datetime.strptime(month_name[:3], '%b').month
            from_date = datetime(int(year), month_number, 1)
            to_date = from_date + relativedelta(months=1, days=-1)
            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(to_date.date(), time.max)
            date_spans.append((start, end))
        return date_spans

    def evaluate_days(self, tokens):
        """
        Evaluates a list of days, possibly with a month year, and returns the corresponding date spans.
        """
        days = []
        # Check if the last token is a number (year)
        if tokens and tokens[-1].type == TokenType.NUMBER:
            year = tokens[-1].value
            tokens = tokens[:-1]  # Remove the year from tokens

        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in Lexer.DAY_ALIASES.values():
                day_full_name = token.value
                days.append(day_full_name)
            idx += 1
        date_spans = []
        lookups = {"monday": dtm.monday, "tuesday": dtm.tuesday, "wednesday": dtm.wednesday, "thursday": dtm.thursday,
                     "friday": dtm.friday, "saturday": dtm.saturday, "sunday": dtm.sunday}
        for day_name in days:
            span = lookups[day_name]()
            date_spans.append((span.start, span.end))
        return date_spans

    def calculate_past(self, number, unit):
        """
        Calculates a past date range based on the specified number and unit.
        """
        if unit == 'day':
            from_date = self.today - timedelta(days=number)
        elif unit == 'week':
            from_date = self.today - timedelta(weeks=number)
        elif unit == 'month':
            from_date = self.today - relativedelta(months=number)
        elif unit == 'year':
            from_date = self.today - relativedelta(years=number)
        else:
            return []
        start = datetime.combine(from_date.date(), time.min)
        end = datetime.combine(self.today.date(), time.max)
        return [(start, end)]

    def calculate_future(self, number, unit):
        """
        Calculates a future date range based on the specified number and unit.
        """
        if unit == 'day':
            to_date = self.today + timedelta(days=number)
        elif unit == 'week':
            to_date = self.today + timedelta(weeks=number)
        elif unit == 'month':
            to_date = self.today + relativedelta(months=number)
        elif unit == 'year':
            to_date = self.today + relativedelta(years=number)
        elif unit == 'quarter':
            to_date = self.today + relativedelta(months=3 * number)
        else:
            return []
        start = datetime.combine(self.today.date(), time.min)
        end = datetime.combine(to_date.date(), time.max)
        return [(start, end)]

    def calculate_this(self, unit):
        """
        Calculates the date range for the current period specified by the unit (day, week, month, year, quarter).
        """
        if unit == 'day':
            date = self.today
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
            return [(start, end)]
        elif unit == 'week':
            # Calculate the start and end of the current week (Monday to Sunday)
            start_date = self.today - timedelta(days=self.today.weekday())
            end_date = start_date + timedelta(days=6)
            start = datetime.combine(start_date.date(), time.min)
            end = datetime.combine(end_date.date(), time.max)
            return [(start, end)]
        elif unit == 'month':
            # Start and end of the current month
            start_date = datetime(self.today.year, self.today.month, 1)
            end_date = start_date + relativedelta(months=1, days=-1)
            start = datetime.combine(start_date.date(), time.min)
            end = datetime.combine(end_date.date(), time.max)
            return [(start, end)]
        elif unit == 'year':
            # Start and end of the current year
            start_date = datetime(self.today.year, 1, 1)
            end_date = datetime(self.today.year, 12, 31)
            start = datetime.combine(start_date.date(), time.min)
            end = datetime.combine(end_date.date(), time.max)
            return [(start, end)]
        elif unit == 'quarter':
            # Start and end of the current quarter
            quarter = (self.today.month - 1) // 3 + 1
            from_month = 3 * (quarter - 1) + 1
            start_date = datetime(self.today.year, from_month, 1)
            end_date = start_date + relativedelta(months=3, days=-1)
            start = datetime.combine(start_date.date(), time.min)
            end = datetime.combine(end_date.date(), time.max)
            return [(start, end)]
        else:
            return []

    def calculate_nth_weekday_in_period(self, n, unit):
        """
        Calculates the date for the nth weekday in the specified period (e.g., '1st Monday in March').
        """
        period_spans = self.calculate_this(unit)
        if not period_spans:
            return []
        period_start = period_spans[0][0]
        period_end = period_spans[0][1]

        # Get the weekday number of today
        weekday_num = self.today.weekday()

        # Use dateutil.relativedelta to find the nth weekday
        nth_weekday_date = period_start + relativedelta(day=1, weekday=weekday_num(n))

        if period_start <= nth_weekday_date <= period_end:
            start = datetime.combine(nth_weekday_date.date(), time.min)
            end = datetime.combine(nth_weekday_date.date(), time.max)
            return [(start, end)]
        else:
            return []
