from typing import List, Callable
import environment

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


class UndefinedExpr(LiteralExpr):
    def __init__(self):
        pass

    def repr(self):
        return 'undefined'

    def __repr__(self):
        return 'UndefinedExpr()'


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

    def __eq__(self, other):
        return isinstance(other, BooleanLiteral) and other.host_value == self.host_value


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
                      'mu': MuExpr,
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

    def __getitem__(self, key):
        return self.subexprs[key]

    def __len__(self):
        return len(self.subexprs)


class CallExpr(CombinationExpr):
    def eval(self, env):
        self.operator = self[0].eval(env)
        if not isinstance(self.operator, CallableExpr):
            raise ValueError(type(self).__name__ + ' not callable')
        ### XXX arity check to be implemented
        # if len(self.operator.args) != len(self) - 1:
        #    raise ValueError('mismatching arguments for ' + self[1]._str)
        if isinstance(self.operator, LambdaExpr):
            return self.lambda_eval(env)
        elif isinstance(self.operator, MuExpr):
            return self.mu_eval(env)
        elif isinstance(self.operator, BuiltinProcedure):
            return self.builtin_eval(env)
        return self.macro_eval(env)

    def bind_and_exec(self, parent_env, call_env) -> LISPExpr:
        """Bind the formal parameters to their values and execute the body.

        parameters:
            call_env   -- the environment in which the CallExpr was called.
            parent_env -- the parent environment of where the body will be
                          executed.
        """
        bindings =  {}
        for formal, actual in zip(self.operator.args.subexprs, self[1:]):
            bindings[formal._str] = actual.eval(call_env)
        exec_env = environment.Environment(parent_env, bindings)
        return self.operator.body.eval(exec_env)

    def lambda_eval(self, env):
        return self.bind_and_exec(self.operator.closure, env)

    def mu_eval(self, env):
        return self.bind_and_exec(env, env)

    def macro_eval(self, env):
        bindings =  {}
        for formal, actual in zip(self.operator.args.subexprs, self[1:]):
            bindings[formal._str] = actual
        body_env = environment.Environment(self.operator.closure, bindings)
        macro_body = self.body.eval(body_env)
        return macro_body.eval(env)

    def builtin_eval(self, env):
        return self.operator.execute([arg.eval(env) for arg in self[1:]], env)


class SpecialFormExpr(CombinationExpr):
    def __init__(self, subexprs):
        assert subexprs[0]._str == self.form_name
        if len(subexprs) != self.nargs:
            raise SyntaxError('invalid number arguments for ' + self.form_name)
        CombinationExpr.__init__(self, subexprs)

class DefineExpr(SpecialFormExpr):
    form_name = 'define'
    nargs = 3

    def eval(self, env):
        """Bind a name to the given value or procedure and return the name.

        >>> from environment import Environment
        >>> from parser import parse_tokens, lexer
        >>> de = parse_tokens(lexer('(define a 2)'))[0]
        >>> de.eval(Environment.GLOBAL)
        Name('a')
        >>> Environment.GLOBAL.bindings
        {'a': IntegerLiteral(2)}
        >>> de = parse_tokens(lexer('(define (f x) (* x 2))'))[0]
        >>> de.eval(Environment.GLOBAL).eval(Environment.GLOBAL).repr()
        '(lambda (x) (* x 2))'
        """
        if isinstance(self[1], Name):
            name, val = self[1], self[2].eval(env)
        else:
            try:
                name = self[1][0]
                args = CombinationExpr(self[1][1:])
                val = LambdaExpr([Name('lambda'), args, self[2]]).eval(env)
            except: raise SyntaxError('bad procedure definition')
        env.bind(name, val)
        return name


class IfExpr(SpecialFormExpr):
    form_name = 'if'
    nargs = 4

    def __init__(self, subexprs):
        if len(subexprs) == 3:
            subexprs += [UndefinedExpr()]
        SpecialFormExpr.__init__(self, subexprs)
        self.predicate, self.consequent, self.alternative = self.subexprs[1:]

    def eval(self, env):
        """
        >>> from parser import lexer, parse_tokens
        >>> from environment import Environment
        >>> import builtin
        >>> builtin.bind_builtins(Environment.GLOBAL)
        >>> parse_tokens(lexer("(if (< 3 2) 'wrong 'right)"))[0].eval(Environment.GLOBAL)
        Name('right')
        >>> parse_tokens(lexer("(if (< 2 3) 'right 'wrong)"))[0].eval(Environment.GLOBAL)
        Name('right')
        """
        if self.predicate.eval(env) != BooleanLiteral('#f'):
            return self.consequent.eval(env)
        return self.alternative.eval(env)


class AndExpr(SpecialFormExpr):
    pass

class OrExpr(SpecialFormExpr):
    pass

class LetExpr(SpecialFormExpr):
    pass

class BeginExpr(SpecialFormExpr):
    pass

class CallableExpr(SpecialFormExpr):
    nargs = 3
    def __init__(self, subexprs):
        SpecialFormExpr.__init__(self, subexprs)
        self.args, self.body = self[1], self[2]

    def eval(self, env):
        return self


class LambdaExpr(CallableExpr):
    form_name = 'lambda'

    def eval(self, env):
        self.closure = env
        return self


class MuExpr(CallableExpr):
    form_name = 'mu'


class DefineMacroExpr(CallableExpr):
    form_name = 'define-macro'

    def eval(self, env):
        self.closure = env
        return self


class BuiltinProcedure(CallableExpr):

    def __init__(self,
            default_name: Name,
            execute: Callable[[List[LISPExpr], 'Environment'], LISPExpr]):
        self.default_name = default_name
        self.execute = execute
    
    def repr(self):
        return '#[{}]'.format(self.default_name)

    def __repr__(self):
        return 'BuiltinProcedure({})'.format(self.default_name._str)

class QuoteExpr(SpecialFormExpr):
    form_name = 'quote'
    nargs = 2

    def eval(self, env):
        """
        >>> import parser
        >>> from environment import Environment
        >>> qe = parser.parse_tokens(parser.lexer("'(* x 2)"))[0]
        >>> qe.eval(Environment.GLOBAL).repr()
        '(* x 2)'
        """
        return self[1]


class DelayExpr(SpecialFormExpr):
    pass

class ConsStreamExpr(SpecialFormExpr):
    pass

class QuasiQuoteExpr(SpecialFormExpr):
    form_name = 'quasiquote'
    nargs = 2

    def eval(self, env):
        """
        >>> import parser
        >>> from environment import Environment
        >>> e1 = parser.parse_tokens(parser.lexer('(define a  2)'))[0]
        >>> e2 = parser.parse_tokens(parser.lexer('(define b  3)'))[0]
        >>> e3 = parser.parse_tokens(parser.lexer(',a'))[0]
        >>> e1.eval(Environment.GLOBAL)
        Name('a')
        >>> e2.eval(Environment.GLOBAL)
        Name('b')
        >>> e3.eval(Environment.GLOBAL)
        IntegerLiteral(2)
        >>> e4 = parser.parse_tokens(parser.lexer(
        ...     '`(a b ,a ,b (a ,a) (b ,b))'))[0]
        >>> e4.eval(Environment.GLOBAL).repr()
        '(a b 2 3 (a 2) (b 3))'
        """
        def partial_unquote(expr):
            if not isinstance(expr, CombinationExpr):
                return expr
            if isinstance(expr.sift(), UnquoteExpr):
                return expr.eval(env)
            return CombinationExpr([partial_unquote(e) for e in expr.subexprs])
        return partial_unquote(self[1])


class SetExpr(SpecialFormExpr):
    pass


class UnquoteExpr(SpecialFormExpr):
    form_name = 'unquote'
    nargs = 2

    def eval(self, env):
        return self[1].eval(env)


class UnquoteSplicingExpr(SpecialFormExpr):
    pass

