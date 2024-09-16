from parser.errors import ParsingError
from parser.lexer import Token, TokenType, Lexer


class ASTNode:
    """
    Base class for nodes in the abstract syntax tree.
    """
    pass


class DateSpan(ASTNode):
    """
    Represents a date span node in the AST, which can be a specific date, relative period, or range.
    """
    def __init__(self, value):
        self.value = value  # Dictionary containing details about the date span


class Parser:
    """
    The Parser class processes the list of tokens and builds an abstract syntax tree (AST).
    It follows the grammar rules to parse date expressions.
    """
    def __init__(self, tokens, text = None):
        self.tokens = tokens
        self.text = text
        self.pos = 0  # Current position in the token list
        self.current_token = self.tokens[self.pos]
        self.ast = None  # Store the abstract syntax tree

    def __str__(self):
        return f"Parser('{self.text}')"
    def __repr__(self):
        return f"Parser('{self.text}')"


    def eat(self, token_type):
        """
        Consumes the current token if it matches the expected token type.
        """
        if self.current_token.type == token_type:
            self.advance()
        else:
            raise ParsingError(
                f'Unexpected token {self.current_token.value!r}. Expected token type {token_type}.',
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )

    def advance(self):
        """
        Advances to the next token.
        """
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token(TokenType.EOF, line=self.current_token.line, column=self.current_token.column)

    def parse(self):
        """
        Parses the tokens and returns a list of statements (each statement is a list of DateSpan nodes).
        """
        try:
            statements = []
            while self.current_token.type != TokenType.EOF:
                date_spans = self.parse_statement()
                statements.append(date_spans)
                if self.current_token.type == TokenType.SEMICOLON:
                    self.eat(TokenType.SEMICOLON)
                else:
                    break  # No more statements
            self.ast = statements
            return statements
        except Exception as e:
            # Raise a ParsingError with position information
            raise ParsingError(str(e), self.current_token.line, self.current_token.column, self.current_token.value)

    def parse_statement(self):
        """
        Parses a single statement, which may contain multiple date spans separated by punctuation or 'and'.
        """
        date_spans = []
        while self.current_token.type != TokenType.EOF and self.current_token.type != TokenType.SEMICOLON:
            node = self.date_span()
            date_spans.append(node)
            if self.current_token.type == TokenType.PUNCTUATION or \
               (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and'):
                self.eat(self.current_token.type)  # Consume ',' or 'and'
            else:
                break  # End of date spans in this statement
        return date_spans

    def date_span(self):
        """
        Parses a date span, which can be a specific date, relative date, range, or special period.
        """
        if self.current_token.type == TokenType.IDENTIFIER:
            if self.current_token.value == 'every':
                return self.iterative_date_span()
            elif self.current_token.value in ['last', 'next', 'past', 'this']:
                return self.relative_date_span()
            elif self.current_token.value == 'since':
                return self.since_date_span()
            elif self.current_token.value in ['between', 'from']:
                return self.date_range()
            elif self.current_token.value in Lexer.MONTH_ALIASES.values():
                return self.month_date_span()
            elif self.current_token.value in Lexer.DAY_ALIASES.values():
                return self.day_date_span()
            # elif self.current_token.value in Lexer.TIME_UNIT_ALIASES.values():
            #     return self.month_date_span()
            else:
                raise ParsingError(
                    f'Unexpected identifier {self.current_token.value!r}',
                    self.current_token.line,
                    self.current_token.column,
                    self.current_token.value
                )

        elif self.current_token.type == TokenType.SPECIAL:
            return self.special_date_span()
        elif self.current_token.type in [TokenType.DATE, TokenType.DATETIME]:
            return self.specific_date_span()
        elif self.current_token.type == TokenType.NUMBER or self.current_token.type == TokenType.ORDINAL:
            return self.relative_date_span()
        else:
            raise ParsingError(
                f'Unexpected token {self.current_token.value!r} of type {self.current_token.type}',
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )

    def iterative_date_span(self):
        """
        Parses an iterative date span, such as 'every Mon, Tue, Wed in this month' or 'every 1st Monday of YTD'.
        """
        self.eat(TokenType.IDENTIFIER)  # Consume 'every'
        tokens = []
        # Optionally consume ordinal and weekdays
        while True:
            if self.current_token.type == TokenType.ORDINAL:
                tokens.append(self.current_token)
                self.eat(TokenType.ORDINAL)
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.DAY_ALIASES.values():
                tokens.append(self.current_token)
                self.eat(TokenType.IDENTIFIER)
                if self.current_token.type == TokenType.PUNCTUATION:
                    self.eat(TokenType.PUNCTUATION)
                elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                    self.eat(TokenType.IDENTIFIER)
            elif self.current_token.type == TokenType.TIME_UNIT and self.current_token.value in Lexer.TIME_UNIT_ALIASES.values():
                tokens.append(self.current_token)
                self.eat(TokenType.TIME_UNIT)
            else:
                break  # No more ordinals or weekdays

        # Expect 'in' or 'of'
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['in', 'of']:
            self.eat(TokenType.IDENTIFIER)
        else:
            raise ParsingError(
                f"Expected 'in' or 'of', got {self.current_token}",
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )
        # Collect period tokens
        period_tokens = []
        while self.current_token.type != TokenType.EOF and \
              not (self.current_token.type == TokenType.PUNCTUATION or
                   self.current_token.type == TokenType.SEMICOLON):
            period_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpan({'type': 'iterative', 'tokens': tokens, 'period_tokens': period_tokens})

    def specific_date_span(self):
        """
        Parses a specific date, possibly with time, and returns a DateSpan node.
        """
        date_value = self.current_token.value
        token_type = self.current_token.type
        self.eat(token_type)
        # Optionally consume a time after the date
        if self.current_token.type == TokenType.TIME:
            time_value = self.current_token.value
            self.eat(TokenType.TIME)
            date_value += ' ' + time_value  # Combine date and time
        return DateSpan({'type': 'specific_date', 'date': date_value})

    def date_range(self):
        """
        Parses a date range expression, such as 'from ... to ...' or 'between ... and ...'.
        """
        self.eat(TokenType.IDENTIFIER)  # Consume 'from' or 'between'
        # Parse the start date expression
        start_tokens = []
        while self.current_token.type != TokenType.EOF and \
              not (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['and', 'to']):
            start_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        # Consume 'and' or 'to'
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['and', 'to']:
            self.eat(TokenType.IDENTIFIER)
        else:
            raise ParsingError(
                f"Expected 'and' or 'to', got {self.current_token.value!r}",
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )
        # Parse the end date expression
        end_tokens = []
        while self.current_token.type != TokenType.EOF and \
              not (self.current_token.type == TokenType.PUNCTUATION or
                   self.current_token.type == TokenType.SEMICOLON or
                   (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and')):
            end_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpan({'type': 'range', 'start_tokens': start_tokens, 'end_tokens': end_tokens})

    def since_date_span(self):
        """
        Parses a 'since' date expression, such as 'since August 2024'.
        """
        self.eat(TokenType.IDENTIFIER)  # Consume 'since'
        tokens = []
        while self.current_token.type != TokenType.EOF and \
              not (self.current_token.type == TokenType.PUNCTUATION or
                   self.current_token.type == TokenType.SEMICOLON):
            tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpan({'type': 'since', 'tokens': tokens})

    def relative_date_span(self):
        """
        Parses a relative date span, such as 'last week' or 'next 3 months'.
        """
        tokens = []
        while self.current_token.type in [TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.ORDINAL, TokenType.TIME_UNIT, TokenType.SPECIAL]:
            tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpan({'type': 'relative', 'tokens': tokens})

    def special_date_span(self):
        """
        Parses a special date span, such as 'today' or 'ytd'.
        """
        token = self.current_token
        self.eat(TokenType.SPECIAL)
        return DateSpan({'type': 'special', 'value': token.value})

    def month_date_span(self):
        """
        Parses a date span that specifies months, such as 'Jan, Feb and August of 2024'.
        """
        tokens = []
        while self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.MONTH_ALIASES.values():
            tokens.append(self.current_token)
            self.eat(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.PUNCTUATION:
                self.eat(TokenType.PUNCTUATION)  # Consume comma or hyphen
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                self.eat(TokenType.IDENTIFIER)
        # Optionally consume 'of' and a year
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'of':
            self.eat(TokenType.IDENTIFIER)
        if self.current_token.type == TokenType.NUMBER:
            tokens.append(self.current_token)  # Append the year
            self.eat(TokenType.NUMBER)
        return DateSpan({'type': 'months', 'tokens': tokens})

    def day_date_span(self):
        """
        Parses a date span that specifies months, such as 'Monday, Tuesday and Friday of this week'.
        """
        # method added by TZ
        tokens = []
        while self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.DAY_ALIASES.values():
            tokens.append(self.current_token)
            self.eat(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.PUNCTUATION:
                self.eat(TokenType.PUNCTUATION)  # Consume comma or hyphen
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                self.eat(TokenType.IDENTIFIER)

        # Optionally consume 'of' and a year
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'of':
            self.eat(TokenType.IDENTIFIER)
        if self.current_token.type == TokenType.NUMBER:
            tokens.append(self.current_token)  # Append the year
            self.eat(TokenType.NUMBER)
        return DateSpan({'type': 'days', 'tokens': tokens})
