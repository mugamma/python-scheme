from typing import List

class LISPExpr:
    """A LISP expression is a LISP list or a single symbol."""
    def __init__(self):
        raise NotImplementedError

    def eval(self, env):
        raise NotImplementedError

    def repr(self) -> str:
        raise NotImplementedError


class SymbolicExpr(LISPExpr):
    @staticmethod
    def create_symbolic_expr(token: str):
        """Factory for creating LISP expressions that are not lists.
        
        A `SymbolicExpr` is either a list or a name.

        pre-condition:
            - the given token is a valid name or literal token.

        >>> SymbolicExpr.create_symbolic_expr('10')
        IntegerLiteral(10)
        >>> SymbolicExpr.create_symbolic_expr('true')
        BooleanLiteral('#t')
        >>> SymbolicExpr.create_symbolic_expr('#f')
        BooleanLiteral('#f')
        >>> SymbolicExpr.create_symbolic_expr('2.2')
        FloatLiteral(2.2)
        >>> SymbolicExpr.create_symbolic_expr('"hello world"')
        StringLiteral('hello world')
        >>> SymbolicExpr.create_symbolic_expr('test')
        Name('test')
        """
        try:
            return LiteralExpr.create_literal_expr(token)
        except ValueError:
            return Name(token)


class Name(SymbolicExpr):
    """Names can refer to values"""

    def __init__(self, construction_token: str):
        """Create a name from the given construction token.
        
        pre-condition:
            - construction_token is a valid LISP name.
        """
        self._str = construction_token

    def eval(self, env):
        try:
            return env[self]
        except KeyError:
            if env.parent is None:
                raise NameError('Unbound name: ' + self._str)
            return self.eval(env.parent)

    def repr(self) -> str:
        return self._str

    def __hash__(self):
        return hash(self._str)

    def __repr__(self):
        return 'Name({})'.format(repr(self._str))


class LiteralExpr(SymbolicExpr):
    """Self-evaluating expressions"""

    @staticmethod
    def create_literal_expr(token: str):
        """Factory for creating literal expressions.

        pre-condition:
            - the given token is a valid literal token.
        """
        if token[0] == '"':
            return StringLiteral(token)
        try:
            return NumericLiteral.create_numeric_literal(token)
        except ValueError:
            if token in ['#f', 'false']:
                return BooleanLiteral('#f')
            elif token in ['#t', 'true']:
                return BooleanLiteral('#t')
            raise

    def eval(self, env):
        return self

    def repr(self):
        return str(self.host_value)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.host_value))


class StringLiteral(LiteralExpr):
    def __init__(self, construction_token: str):
        """Create a string literal from the given token.
        
        pre-condition:
            - construction_token is a valid string literal token: "[^"]*"
        """
        self.host_value = construction_token[1:-1]


class BooleanLiteral(LiteralExpr):
    def __init__(self, construction_token: str):
        """Create a boolean literal from the given token.
        
        pre-condition:
            - construction_token is a valid boolean literal token: #t | #f
        """
        self.host_value = construction_token == '#t'

    def repr(self):
        return '#t' if self.host_value else '#f'

    def __repr__(self):
        return 'BooleanLiteral(' +("'#t'" if self.host_value else "'#f'") +')'


class NumericLiteral(LiteralExpr):
    @staticmethod
    def create_numeric_literal(token: str):
        try:
            return IntegerLiteral(token)
        except ValueError:
            return FloatLiteral(token)


class IntegerLiteral(NumericLiteral):
    def __init__(self, construction_token):
        """Create an integer literal from the given token.
        
        pre-condition:
            - construction_token is a valid integer literal token.
        """
        self.host_value = int(construction_token)


class FloatLiteral(NumericLiteral):
    def __init__(self, construction_token):
        """Create a float literal from the given token.
        
        pre-condition:
            - construction_token is a valid float literal token.
        """
        self.host_value = float(construction_token)


class CombinationExpr(LISPExpr):
    def __init__(self, subexprs: List[LISPExpr]):
        self.subexprs = subexprs

    def eval(self, env):
        return self.sift().eval(env)

    def repr(self):
        return '(' + ' '.join(subexp.repr() for subexp in self.subexprs) + ')'

    def sift(self):
        """Sift down a general combination expression to a subclass.

        Used to call the correct eval method.
        """
        expr_class = {'define': DefineExpr,
                      'if': IfExpr,
                      'and': AndExpr,
                      'or': OrExpr,
                      'let': LetExpr,
                      'begin': BeginExpr, 
                      'lambda': LambdaExpr,
                      'Mu': MuExpr,
                      'quote': QuoteExpr,
                      'cons-stream': ConsStreamExpr,
                      'set!': SetExpr, 
                      'quasiquote': QuasiQuoteExpr,
                      'unquote': UnquoteExpr,
                      'unquote-splicing': UnquoteSplicingExpr,
                      'define-macro': DefineMacroExpr}
        try:
            return expr_class[self.subexprs[0]._str](self.subexprs)
        except:
            return CallExpr(self.subexprs)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.subexprs))

class CallExpr(CombinationExpr):
    pass

class DefineExpr(CombinationExpr):
    pass

class IfExpr(CombinationExpr):
    pass

class AndExpr(CombinationExpr):
    pass

class OrExpr(CombinationExpr):
    pass

class LetExpr(CombinationExpr):
    pass

class BeginExpr(CombinationExpr):
    pass

class LambdaExpr(CombinationExpr):
    pass

class MuExpr(CombinationExpr):
    pass

class QuoteExpr(CombinationExpr):
    pass

class DelayExpr(CombinationExpr):
    pass

class ConsStreamExpr(CombinationExpr):
    pass

class QuasiQuoteExpr(CombinationExpr):
    pass

class SetExpr(CombinationExpr):
    pass

class UnquoteExpr(CombinationExpr):
    pass

class UnquoteSplicingExpr(CombinationExpr):
    pass

class DefineMacroExpr(CombinationExpr):
    pass
