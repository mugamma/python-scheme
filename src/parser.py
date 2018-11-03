from typing import List

def lexer(inpt: str) -> List[str]:
    """Return the list of tokens found in `inpt`.

    A token is defined as follows:
       token: brackets | str | sugar | name
       brackets: ( | )
       str: "[^"]*"
       sugar: ' | ` | ,
       name: [^()'"`,]+

    >>> lexer('10')
    ['10']
    >>> lexer('(define this#is#a~!@#$%^&*_name 5)')
    ['(', 'define', 'this#is#a~!@#$%^&*_name', '5', ')']
    >>> lexer('(define not_good_for_you \'sugar)')
    ['(', 'define', 'not_good_for_you', '\'', 'sugar', ')']
    >>> lexer('(define string_cheese "cheesy")')
    ['(', 'define', 'string_cheese', '"cheesy"', ')']
    >>> lexer('(+(eval 2)(eval 3))')
    ['(', '+', '(', 'eval', '2', ')' , '(', 'eval', '2', ')' ')']
    >>> lexer('(do-something ;something big\n  \'unqoute)')
    ['(' 'do-something', '\'', 'unqoute', ')']
    """
