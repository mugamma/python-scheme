import expr

## Core Interpreter

BUILTINS = []

def lisp_builtin(*names):
    def decorator(exec_func):
        for name in names:
            BUILTINS.append(expr.BuiltinProcedure(expr.Name(name), exec_func))
        return exec_func
    return decorator

@lisp_builtin('+')
def __add_exec(args, env):
    """Add the arguments.

    Arguemts must be of numeric type.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer('(+ 2 3)'))[0].eval(Environment.GLOBAL)
    IntegerLiteral(5)
    """
    res = sum(arg.host_value for arg in args)
    return expr.NumericLiteral.create_numeric_literal(res)

@lisp_builtin('-')
def __sub_exec(args, env):
    """Subtract the rest of the argument arguments from the first argument.

    Arguemts must be of numeric type.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer('(- 5 3)'))[0].eval(Environment.GLOBAL)
    IntegerLiteral(2)
    """
    res = args[0].host_value + sum(-arg.host_value for arg in args[1:])
    return expr.NumericLiteral.create_numeric_literal(res)

@lisp_builtin('*')
def __sub_exec(args, env):
    """Multiply the arguments.

    Arguemts must be of numeric type.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer('(* 5 3 2)'))[0].eval(Environment.GLOBAL)
    IntegerLiteral(30)
    """
    from functools import reduce
    from operator import mul
    res = reduce(mul, [arg.host_value for arg in args])
    return expr.NumericLiteral.create_numeric_literal(res)

@lisp_builtin('/')
def __sub_exec(args, env):
    """Divide the first argument by the rest of the arguments.

    Arguemts must be of numeric type.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer('(/ 18 3 2)'))[0].eval(Environment.GLOBAL)
    IntegerLiteral(3)
    """
    from functools import reduce
    from operator import truediv
    res = reduce(truediv, [arg.host_value for arg in args])
    return expr.NumericLiteral.create_numeric_literal(res)

@lisp_builtin('=')
def __equalsign_exec(args, env):
    a, b = [arg.host_value for arg in args]
    return expr.BooleanLiteral('#t' if a == b else '#f')

@lisp_builtin('<')
def __lt_exec(args, env):
    a, b = [arg.host_value for arg in args]
    return expr.BooleanLiteral('#t' if a < b else '#f')

@lisp_builtin('apply')
def __apply_exec(args, env):
    """Apply the given function to the argument list.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer("(apply + '(1 2 3 4))"))[0].eval(Environment.GLOBAL)
    IntegerLiteral(10)
    """
    call_subexps = [args[0]] + args[1].subexprs
    return expr.CallExpr(call_subexps).eval(env)

@lisp_builtin('display')
def __display_exec(args, env):
    """Prints its argument.
    
    If the argument is a Scheme string, it will be output without quotes. A new
    line will not be automatically included.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer('(display (+ 2 3))'))[0].eval(Environment.GLOBAL)
    5UndefinedExpr()
    >>> parse_tokens(lexer("(display 'x)"))[0].eval(Environment.GLOBAL)
    xUndefinedExpr()
    >>> parse_tokens(lexer("(display (lambda (x) (+ x 2)))"))[0].eval(Environment.GLOBAL)
    (lambda (x) (+ x 2))UndefinedExpr()
    >>> parse_tokens(lexer("(display (display 2))"))[0].eval(Environment.GLOBAL)
    2undefinedUndefinedExpr()
    >>> parse_tokens(lexer("(display '(1 2))"))[0].eval(Environment.GLOBAL)
    (1 2)UndefinedExpr()
    """
    print(args[0].repr(), end='')
    return expr.UndefinedExpr()

@lisp_builtin('eval')
def __eval_exec(args, env):
    """
    Evaluate its argument in env.

    >>> import builtin
    >>> from parser import lexer, parse_tokens
    >>> from environment import Environment
    >>> builtin.bind_builtins(Environment.GLOBAL)
    >>> parse_tokens(lexer("(eval '(+ 1 2))"))[0].eval(Environment.GLOBAL)
    IntegerLiteral(3)
    """
    return args[0].eval(env)

@lisp_builtin('exit')
def __exit_exec(args, env):
    """Exits the interpreter."""
    exit()

@lisp_builtin('cons')
def __cons_exec(args, env):
    return expr.CombinationExpr(args)

@lisp_builtin('car')
def __car_exec(args, env):
    return args[0][0]

@lisp_builtin('cdr')
def __cdr_exec(args, env):
    return expr.CombinationExpr(args[0][1:])

@lisp_builtin('load')
def __load_exec(args, env):
    from parser import lexer, parse_tokens
    with open(args[0]._str + '.scm') as source_file:
        source = ''.join(line for line in source_file)
    for expression in parse_tokens(lexer(source)):
        expression.eval(env)
    return expr.UndefinedExpr()

def bind_builtins(env):
    for procedure in BUILTINS:
        env.bind(procedure.default_name, procedure)
