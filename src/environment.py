from expr import Name, LISPExpr

class Environment:
    """An execution environment"""

    def __init__(self, parent, bindings={}):
        """Create an environment.

        Attributes:
          bindings -- a dictionary of str -> expr.LISPExpr
          parent   -- another environment
        """
        self.bindings = bindings
        self.parent = parent

    def bind(self, name: Name, value: LISPExpr):
        if not isinstance(name, Name):
            raise ValueError('cannot bind value to non-name.')
        self.bindings[name._str] = value

    def __getitem__(self, name):
        return self.bindings[name._str]

Environment.GLOBAL = Environment(None)
