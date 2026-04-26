# this file containts AST node definitions for expressions, an eval method for
# intepreting expressions to values, and run method for showing values to the user.
from dataclasses import dataclass
import csv
import os

type Expr = Lit | Add | Sub | Mul | Div | Neg | And | Or | Not | Eq | Lt | If | Name| Let | TableLit | SelectExpr | JoinExpr

@dataclass
class Lit():
    value: int | bool
    def __str__(self):
        return f"{self.value}"
    
@dataclass
class Add():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} + {self.right})"
    
@dataclass
class Sub():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} - {self.right})"
    
@dataclass
class Mul():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} * {self.right})"

@dataclass
class Div():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} / {self.right})"
    
@dataclass
class Neg():
    operand: Expr
    def __str__(self):
        return f"(-{self.operand})"
    
@dataclass
class And():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} and {self.right})"
    
@dataclass
class Or():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} or {self.right})"

@dataclass
class Not():
    operand: Expr
    def __str__(self):
        return f"(Not {self.operand})"
    
@dataclass
class Eq():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} == {self.right})"
    
@dataclass
class Lt():
    left: Expr
    right: Expr
    def __str__(self):
        return f"({self.left} < {self.right})"
    
@dataclass
class If():
    cond: Expr
    then: Expr
    else_: Expr
    def __str__(self):
        return f"({self.cond} then {self.then} else {self.else_})"
    
@dataclass
class Name():
    var: str
    def __str__(self):
        return self.var
    
@dataclass
class Let():
    var: str
    expr:Expr
    body: Expr
    def __str__(self):
        return f"(Let {self.var} = {self.expr} in {self.body})"
    
# my relation schemas, where i will select join tables
@dataclass
class TableLit():
    filename: str
    def __str__(self):
        return f"Table({self.filename})"

@dataclass
class SelectExpr():
    colums: list[str]
    table: Expr
    def __str__(self):
        return f"(SELECT {self.colums} FROM {self.table})"

@dataclass
class JoinExpr():
    left: Expr
    right: Expr
    column: str
    def __str__(self):
        return f"(JOIN {self.left} AND {self.right} ON {self.column})"
    

# eval methords, settting up the environment

type Binding[V] = tuple[str, V]
type Env[V] = tuple[Binding[V], ...]

from typing import Any
emptyEnv: Env[Any] = ()

def extendEnv[V](name: str, value: V, env: Env[V]) -> Env[V]:
    return ((name, value),) + env

def lookupEnv[V](name: str, env: Env[V]) -> V | None:
    match env:
        case ((n, v), *rest):
            if n == name:
                return v
            else:
                return lookupEnv(name, rest)  # type: ignore
        case _:
            return None

class EvalError(Exception):
    pass

# shema
@dataclass
class Table():
    columns: list[str]
    rows: list[dict]
    def __str__(self):
        if not self.rows:
            return "(The empty table with columns: " + ", ".join(self.columns) + ")"
        
        col_widths = {col: max(len(col), max(len(str(row[col])) for row in self.rows)) for col in self.columns}
        
        header = " | ".join(col.ljust(col_widths[col]) for col in self.columns)
        
        divider = "-+-".join("-" * col_widths[col] for col in self.columns)
        
        data_rows = [" | ".join(str(row[col]).ljust(col_widths[col]) for col in self.columns) for row in self.rows]
        
        return "\n".join([header, divider] + data_rows)
    
# evaluation stars here
def eval(e: Expr) -> Any:
    return evalInEnv(emptyEnv, e)

def evalInEnv(env: Env[Any], e: Expr) -> Any:
    match e:

        #Arithmtic 
        case Add(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)) if not isinstance(lv, bool) and not isinstance(rv, bool):
                    return lv + rv
                case _:
                    raise EvalError("only integers for the addition operands")

        case Sub(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)) if not isinstance(lv, bool) and not isinstance(rv, bool):
                    return lv - rv
                case _:
                    raise EvalError("only integers for the substration operands")

        case Mul(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)) if not isinstance(lv, bool) and not isinstance(rv, bool):
                    return lv * rv
                case _:
                    raise EvalError("only integers for the multiplication operands ")

        case Div(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)) if not isinstance(lv, bool) and not isinstance(rv, bool):
                    if rv == 0:
                        raise EvalError("division by zero")
                    return lv // rv
                case _:
                    raise EvalError("only integers for the division operands")

        case Neg(operand):
            match evalInEnv(env, operand):
                case int(i) if not isinstance(i, bool):
                    return -i
                case _:
                    raise EvalError("only integers for the negation operands")

        #Boolean
        case And(l, r):
            lv = evalInEnv(env, l)
            match lv:
                case bool(b):
                    if not b:
                        return False 
                    match evalInEnv(env, r):
                        case bool(rv):
                            return rv
                        case _:
                            raise EvalError("only boolean operands for 'and'")
                case _:
                    raise EvalError("only boolean operands for 'and'")

        case Or(l, r):
            lv = evalInEnv(env, l)
            match lv:
                case bool(b):
                    if b:
                        return True  
                    match evalInEnv(env, r):
                        case bool(rv):
                            return rv
                        case _:
                            raise EvalError("only boolean operands for 'or'")
                case _:
                    raise EvalError("only boolean operands for 'or'")

        case Not(operand):
            match evalInEnv(env, operand):
                case bool(b):
                    return not b
                case _:
                    raise EvalError("only boolean operands for 'not'")

        #Comparisons 
        case Eq(l, r):
            lv = evalInEnv(env, l)
            rv = evalInEnv(env, r)
            if type(lv) != type(rv):
                return False
            match (lv, rv):
                case (Table(), Table()):
                    return lv.columns == rv.columns and lv.rows == rv.rows
                case _:
                    return lv == rv

        case Lt(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)) if not isinstance(lv, bool) and not isinstance(rv, bool):
                    return lv < rv
                case _:
                    raise EvalError("only integer operands for '<'")

        #Conditional
        case If(cond, then, else_):
            match evalInEnv(env, cond):
                case bool(b):
                    if b:
                        return evalInEnv(env, then)
                    else:
                        return evalInEnv(env, else_)
                case _:
                    raise EvalError("condition for 'if' must be a boolean")

        #Variables and binding
        case Name(var):
            v = lookupEnv(var, env)
            if v is None:
                raise EvalError(f"unbound variable '{var}'")
            return v

        case Let(var, expr, body):
            v = evalInEnv(env, expr)
            newEnv = extendEnv(var, v, env)
            return evalInEnv(newEnv, body)

        
        case TableLit(filename):
            if not os.path.exists(filename):
                raise EvalError(f"file not found: '{filename}'")
            with open(filename, newline='') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                if columns is None:
                    raise EvalError(f"'{filename}' is empty")
                rows = [dict(row) for row in reader]
            return Table(list(columns), rows)

        case SelectExpr(columns, table):
            match evalInEnv(env, table):
                case Table(cols, rows):
                    for col in columns:
                        if col not in cols:
                            raise EvalError(f"column '{col}' not found in table")
                    new_rows = [{col: row[col] for col in columns} for row in rows]
                    return Table(columns, new_rows)
                case _:
                    raise EvalError("SELECT requires a table operand")

        case JoinExpr(left, right, column):
            match (evalInEnv(env, left), evalInEnv(env, right)):
                case (Table(lcols, lrows), Table(rcols, rrows)):
                    if column not in lcols:
                        raise EvalError(f"column '{column}' is not in left table")
                    if column not in rcols:
                        raise EvalError(f"column '{column}' is not in right table")
                    new_cols = lcols + [c for c in rcols if c != column]
                    new_rows = []
                    for lr in lrows:
                        for rr in rrows:
                            if lr[column] == rr[column]:
                                merged = dict(lr)
                                for c in rcols:
                                    if c != column:
                                        merged[c] = rr[c]
                                new_rows.append(merged)
                    return Table(new_cols, new_rows)
                case _:
                    raise EvalError("JOIN requires two table operands")

        case Lit(value):
            match value:
                case int(i):
                    return i
                case bool(b):
                    return b
                case _:
                    raise EvalError(f"unknown literal type: {value}")
                
# run
def run(e: Expr) -> None:
    print(f"\nExpression: {e}")
    try:
        result = eval(e)
        match result:
            case int(i):
                print(f"Result: {i}")
            case bool(b):
                print(f"Result: {b}")
            case Table():
                print(f"Result:\n{result}")
                
                with open("answer.csv", "w", newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=result.columns)
                    writer.writeheader()
                    writer.writerows(result.rows)
                print(f"(also saved to answer.csv)")
    except EvalError as err:
        print(f"Error: {err}")



# additional testing specifically for my schemas.
# Test 1: load a table from a csv file
run(TableLit("students.csv"))

# Test 2: select specific columns from a table
run(SelectExpr(["name", "gpa"], TableLit("students.csv")))

# Test 3: join two tables on a shared column
run(JoinExpr(TableLit("students.csv"), TableLit("classes.csv"), "id"))

# Test 4: join then select 
run(SelectExpr(["name", "course"],
        JoinExpr(TableLit("students.csv"),
                 TableLit("classes.csv"),
                 "id")))

# Test 5: use let to bind a table to a variable and reuse it
run(Let("students", TableLit("students.csv"),
        SelectExpr(["name", "gpa"], Name("students"))))


# Test 9: equality comparison on tables
run(Eq(TableLit("students.csv"), TableLit("students.csv")))

# Test 10: error handling — bad column name
run(SelectExpr(["age"], TableLit("students.csv")))


'''
# domain specific extenxtion:
values:   Table, my tables consists of med cumns and rows of data,
          each row is represented as a python dictionary mapping column names to string values.
literals: TableLit, loads a .csv file from disk and returns it as a
          Table value. The first row of the csv file is treated as column headers.
perators: SelectExpr(columns, table), takes a list of column names and a table
          expression, and returns a new table containing only those columns.
          Raises an error if any column name is not present in the table.
          JoinExpr(left, right, column), performs an inner join on two table
          expressions over a shared column name. Returns a new table containing
          all rows where the join column values match. Raises an error if the
          column is not present in both tables.
Equality: Two tables are equal if they have the same columns in the same order
          and the same rows in the same order.

'''

