class ParsingError(Exception):
    """
    Exception raised when a parsing error occurs, including position and token information.
    """
    def __init__(self, message, line=0, column=0, token_value=None):
        super().__init__(message)
        self.line = line
        self.column = column
        self.token_value = token_value

    def __str__(self):
        return f"{super().__str__()} (Line: {self.line}, Column: {self.column}, Token: {self.token_value!r})"


class EvaluationError(Exception):
    """
    Exception raised when an evaluation error occurs.
    """
    def __init__(self, message, line=0, column=0, token_value=None):
        super().__init__(message)
        self.line = line
        self.column = column
        self.token_value = token_value

    def __str__(self):
        return f"{super().__str__()} (Line: {self.line}, Column: {self.column}, Token: {self.token_value!r})"
