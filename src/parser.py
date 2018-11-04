from typing import List

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
    >>> lexer('(define string_cheese "cheesy")')
    ['(', 'define', 'string_cheese', '"cheesy"', ')']
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
    return inpt[:quote_loc + 1], inpt[quote_loc + 1:]

def extract_symbol(inpt: str) -> (str, str):
    """Remove and return the LISP symbol string in the beginning of the inpt.

    pre-condition:
      - inpt starts with a valid LISP symbol string: [^\(\)';`,#\s]*
    
    >>> extract_symbol('1337!$%&*/:<=>?@^_~+-.is_valid 23')
    ('1337!$%&*/:<=>?@^_~+-.is_valid', ' 23')
    """
    end_loc = 0
    is_valid = lambda c: c.isalnum() or c in '!$%&*/:<=>?@^_~+-.'
    while end_loc < len(inpt) and is_valid(inpt[end_loc]):
        end_loc += 1
    return inpt[:end_loc], inpt[end_loc:]
