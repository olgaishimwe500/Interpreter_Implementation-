from interp import (Add, Sub, Mul, Div, Neg, Lit, Let, Letfun, App, 
                    Name, And, Or, Not, Eq, Lt, If, TableLit, 
                    SelectExpr, JoinExpr, Expr, run, eval)
from lark import Lark, Token, ParseTree, Transformer
from lark.exceptions import VisitError
from pathlib import Path

parser = Lark(Path('expr.lark').read_text(), start='expr', parser='earley', ambiguity='explicit')

class ParserError(Exception):
    pass

def parse(s: str) -> ParseTree:
    try:
        return parser.parse(s)
    except Exception as e:
        raise ParserError(e)
    
class AmbiguousParse(Exception):
    pass

#transfomer
class ToExpr(Transformer[Token, Expr]):
    #the arithmetic
    def plus(self, args):
        return Add(args[0], args[1])
    def minus(self, args):
        return Sub(args[0], args[1])
    def times(self, args):
        return Mul(args[0], args[1])
    def divide(self, args):
        return Div(args[0], args[1])
    def neg(self, args):
        return Neg(args[0])
    def int(self, args):
        return Lit(int(args[0].value))
    
    #boolen
    def or_op(self, args):
        return Or(args[0], args[1])
    def and_op(self, args):
        return And(args[0], args[1])
    def not_op(self, args):
        return Not(args[0])
    
    #comparisons
    def eq(self, args):
        return Eq(args[0], args[1])
    def lt(self, args):
        return Lt(args[0], args[1])
    
    #my conds
    def if_expr(self, args):
        return If(args[0], args[1], args[2])
    
    def id(self, args):
        match args[0].value:
            case 'true':
                return Lit(True)
            case 'false':
                return Lit(False)
            case n:
                return Name(n)
    def let(self, args):
        return Let(args[0].value, args[1], args[2])
    def letfun(self,args):
        return Letfun(args[0].value, args[1].value, args[2], args[3])
    def app(self, args):
        return App(args[0], args[1])
    
    #domain specifs
    def table_lit(self, args):
        filename = args[0].value[1:-1]
        return TableLit(filename)
    
    def select_expr(self, args):
        # columns = [str(a.value) for a in args[:-1]]
        table = args[-1]
        # id_list_tree = args[0]
        columns = [str(token) for token in args[:-1]]
        return SelectExpr(columns, table)
    
    def join_expr(self, args):
        return JoinExpr(args[0], args[1], args[2].value)
    
    def _ambig(self, _):
        raise AmbiguousParse()
    
def genAST(t: ParseTree) -> Expr:
    try:
        return ToExpr().transform(t)
    except VisitError as e:
        if isinstance(e.orig_exc, AmbiguousParse):
            raise AmbiguousParse()
        else:
            raise e

#parse adn run
def parse_and_run(s: str) -> None:
    try:
        t = parse(s)
        ast = genAST(t)
        run (ast)
    except AmbiguousParse:
        print("ambiguous parse")
    except ParserError as e:
        print("parse error: ")
        print(e)

def driver():
    while True:
        try:
            s = input('expr: ')
            t = parse(s)
            ast = genAST(t)
            run(ast)
        except AmbiguousParse:
            print("ambiguous parse")
        except AmbiguousParse:
            print("ambiguous parse")
        except ParserError as e:
            print("parse error: ")
            print(e)
        except EOFError:
            break

#tests
# Test 1: load a table using concrte syntax
parse_and_run('"students.csv"')

# Test 2: select columns using concrte syntax
parse_and_run('select [name, gpa] from "students.csv" end')

# Test 3: join two tables using concrete syntax
parse_and_run('join "students.csv" and "classes.csv" on id end')

# Test 4: join then select chained togetherr
parse_and_run('select [name, course] from join "students.csv" and "classes.csv" on id end end')

# Test 5: let binding with a table
parse_and_run('let s = "students.csv" in select [name, gpa] from s end end')

# Test 6: equality compraison on tables
parse_and_run('"students.csv" == "students.csv"')

# Test 7: error handling — bad column name
parse_and_run('select [age] from "students.csv" end')

# Test 8: letfun with arithmetic
parse_and_run('letfun double x = x + x in double(10) end')

# Test 9: letfun with conditional
parse_and_run('letfun max a = if a < 10 then 10 else a end in max(5) end')
 