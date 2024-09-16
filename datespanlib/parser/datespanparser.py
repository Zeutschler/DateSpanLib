from datespanlib.parser.errors import ParsingError, EvaluationError
from datespanlib.parser.evaluator import Evaluator
from datespanlib.parser.lexer import Lexer
from datespanlib.parser.parser import Parser


# Todos:
# - use the DateSpan class for interal calculations
#
# - Add a parameter how to handle 'last' and 'next':
#   To full month/quarter/year (default) or relative to today (current implementation)
#   method to change: Evaluator.evaluate_relative() -> calculate_past()
#
# - ensure all methods of the evaluator resolve the correct date spans
#
# - harmonize error handling


class DateSpanParser:
    """
    The DateSpanParser class serves as the main interface. It takes an input string,
    tokenizes it, parses the tokens into an AST, and evaluates the AST to produce date spans.
    """
    def __init__(self, text):
        self.text = str(text).strip()
        self.lexer = None
        self.parser = None
        self.evaluator = None

    def parse(self) -> list:
        """
        Parses the input text and evaluates the date spans.
        """
        if not self.text:
            raise ParsingError('Input text cannot be empty.', line=1, column=0, token_value='')

        self.lexer = Lexer(self.text)
        self.parser = Parser(self.lexer.tokens, self.text)
        try:
            statements = self.parser.parse()
            self.evaluator = Evaluator(statements)
            self.evaluator.evaluate()
            return self.evaluator.evaluated_spans

        except (ParsingError, EvaluationError) as e:
            # Re-raise the exception to be caught in tests or by the caller
            raise e

    @property
    def tokens(self):
        """
        Returns the list of tokens from the lexer.
        """
        return self.lexer.tokens if self.lexer else []

    @property
    def parse_tree(self):
        """
        Returns the abstract syntax tree from the parser_old.
        """
        return self.parser.ast if self.parser else None

    @property
    def date_spans(self):
        """
        Returns the evaluated date spans from the evaluator.
        """
        return self.evaluator.evaluated_spans if self.evaluator else []