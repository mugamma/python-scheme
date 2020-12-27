import builtin
from parser import lexer, parse_tokens
from environment import Environment
import sys

if __name__ == '__main__':
    sys.setrecursionlimit(1000000)
    builtin.bind_builtins(Environment.GLOBAL)
    try:
        while True:
            try:
                for exp in parse_tokens(lexer(input('>'))):
                    print(exp.eval(Environment.GLOBAL).repr())
            except BaseException as e:
                if isinstance(e, EOFError): raise e
                print(type(e).__name__ + ': ' + str(e))
    except EOFError:
        print('\nEnd of input stream reached.\nMoriturus te saluto.')
