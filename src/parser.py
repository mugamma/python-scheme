from typing import List

from expr import *

def lexer(inpt: str) -> List[str]:
    """Return the list of tokens found in `inpt`.

    A token is defined as follows:
       token: brackets | str | sugar | name | pound_start
       brackets: ( | )
       str: "[^"]*"
       sugar: ' | ` | ,
       name: [^()#'"`,]+
       pound_start: #.
    the way `pound_start` is defined is in compliance with the 61A scheme
    behavior.

    >>> lexer('10')
    ['10']
    >>> lexer('(define this_is_a~!@_$%^&*_name 5)')
    ['(', 'define', 'this_is_a~!@_$%^&*_name', '5', ')']
    >>> lexer("(define not_good_for_you 'sugar)")
    ['(', 'define', 'not_good_for_you', "'", 'sugar', ')']
    >>> lexer('(DEFINE string_CHEESE "chEESy")')
    ['(', 'define', 'string_cheese', '"chEESy"', ')']
    >>> lexer('(+(eval 2)(eval 3))')
    ['(', '+', '(', 'eval', '2', ')', '(', 'eval', '3', ')', ')']
    >>> lexer("(do-something ;something big\\n  'unqoute)")
    ['(', 'do-something', "'", 'unqoute', ')']

    """
    tokens = []
    while inpt:
        token, inpt = extract_token(inpt)
        if token is not None:
            tokens.append(token)
    return tokens

def extract_token(inpt: str) -> (str, str):
    """Return the first token (or `None`) along with the rest of `inpt`.

    This function removes any delimiters in the beginning of its output. a
    delimiter is a comment or whitespace.
    
    >>> extract_token('10')
    ('10', '')
    >>> extract_token('\\n')
    (None, '')
    >>> extract_token('')
    (None, '')
    >>> extract_token('(+(eval 2)(eval 3))')
    ('(', '+(eval 2)(eval 3))')
    >>> extract_token(';do this next\\n this)')
    ('this', ')')
    """
    inpt = inpt.lstrip()
    if inpt == '': return (None, '')
    if inpt[0] == ';':
        return extract_token(strip_comment(inpt))
    if inpt[0] in '()\'`,': # bracket or sugar
        return inpt[0], inpt[1:]
    if inpt[0] == '"':
        return extract_string_literal(inpt)
    if inpt[0] == '#': # 61A scheme pound
        return inpt[:2], inpt[2:]
    return extract_symbol(inpt)

def strip_comment(inpt: str) -> str:
    """Remove the comment in the beginning of the inpt.

    pre-condition:
      - inpt starts with a comment: ;.*\\n
    
    >>> strip_comment('; some comment\\n blah blah')
    ' blah blah'
    """
    return inpt[inpt.find('\n') + 1:]

def extract_string_literal(inpt: str) -> (str, str):
    """Remove and return the string litteral in the beginning of the inpt.

    pre-condition:
      - inpt starts with a string literal: "[^"]*"
    
    >>> extract_string_literal('"some string" blah blah')
    ('"some string"', ' blah blah')
    """
    quote_loc = inpt.find('"', 1)
    if quote_loc == -1:
        raise SyntaxError('malformed string literal: ' + inpt)
    return inpt[:quote_loc + 1], inpt[quote_loc + 1:]

def extract_symbol(inpt: str) -> (str, str):
    """Remove and return the LISP symbol string in the beginning of the inpt.

    pre-condition:
      - inpt starts with a valid LISP symbol string: [^\(\)';`,#\s]*

    post-condition:
      - returned symbol token is case normalized (lower case).
    
    >>> extract_symbol('1337!$%&*/:<=>?@^_~+-.IS_valid 23')
    ('1337!$%&*/:<=>?@^_~+-.is_valid', ' 23')
    """
    end_loc = 0
    is_valid = lambda c: c.isalnum() or c in '!$%&*/:<=>?@^_~+-.'
    while end_loc < len(inpt) and is_valid(inpt[end_loc]):
        end_loc += 1
    return inpt[:end_loc].lower(), inpt[end_loc:]

def parse_tokens(tokens: List[str]) -> List[LISPExpr]:
    """Return a list of LISP expressions parsed from the input token list.
    
    >>> parse_tokens(lexer('(+ 2 3)'))
    [CombinationExpr([Name('+'), IntegerLiteral(2), IntegerLiteral(3)])]
    >>> parse_tokens(lexer('(+(eval 2)(eval 3))'))
    [CombinationExpr([Name('+'), CombinationExpr([Name('eval'), IntegerLiteral(2)]), CombinationExpr([Name('eval'), IntegerLiteral(3)])])]
    >>> parse_tokens(lexer("(define not_good_for_you 'sugar)"))
    [CombinationExpr([Name('define'), Name('not_good_for_you'), CombinationExpr([Name('quote'), Name('sugar')])])]
    >>> parse_tokens(lexer("`(is partially ,ed)"))[0].repr()
    '(quasiquote (is partially (unquote ed)))'
    """
    exprs = []
    while tokens:
        expr, tokens = extract_expr(tokens)
        exprs.append(expr)
    return exprs

def extract_expr(tokens: List[str]) -> (LISPExpr, List[str]):
    """Parse and return the next LISP expression in `tokens`.

    The second value in the reutrned tuple will be the rest of the tokens.
    """
    if not tokens:
        return None, tokens
    if tokens[0] == ')':
        raise SyntaxError('Unexpected token: )')
    elif tokens[0] == '(':
        return extract_combination_expr(tokens)
    elif tokens[0] in "'`,":
        return extract_sugar_expr(tokens)
    else:
        return extract_symbolic_expr(tokens)

def extract_symbolic_expr(tokens: List[str]) -> (SymbolicExpr, List[str]):
    """Parse and return the next non-list LISP expression in `tokens`.

        pre-conditions:
          - the first token in `tokens` must parse to a valid non-list LISP
            expression.
    """
    return SymbolicExpr.create_symbolic_expr(tokens[0]), tokens[1:]

def extract_sugar_expr(tokens: List[str]) -> (CombinationExpr, List[str]):
    """Parse and return the next (quasi/un)quote LISP expression in `tokens`.

        pre-conditions:
          - the first token in `tokens` must be one of "`", "'", or ",".
    """
    opname = {"'": 'quote', '`': 'quasiquote', ',': 'unquote'}[tokens[0]]
    operand, rest = extract_expr(tokens[1:])
    if operand is None:
        raise SyntaxError('no operand for ' + opname)
    return CombinationExpr([Name(opname), operand]), rest

def extract_combination_expr(tokens):
    subexpr_tokens, rest_tokens = extract_combination_tokens(tokens)
    return CombinationExpr(parse_tokens(subexpr_tokens[1:-1])), rest_tokens

def extract_combination_tokens(tokens):
    subexpr_tokens, depth = [], 0
    for i, token in enumerate(tokens):
        if token in ['(', ')']:
            depth += 1 if token == '(' else -1
        subexpr_tokens.append(token)
        if depth == 0: break
    else:
        raise SyntaxError('Unbalanced combination expression')
    return subexpr_tokens, tokens[i+1:]
