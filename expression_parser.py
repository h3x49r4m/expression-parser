import ast

# Map AST operator types to their string representations
OPERATOR_MAP = {
    ast.Add: '+',
    ast.Sub: '-',
    ast.Mult: '*',
    ast.Div: '/',
    ast.Mod: '%',
    ast.Pow: '**',
    ast.LShift: '<<',
    ast.RShift: '>>',
    ast.BitOr: '|',
    ast.BitXor: '^',
    ast.BitAnd: '&',
    ast.FloorDiv: '//',

    ast.Eq: '==',
    ast.NotEq: '!=',
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Is: 'is',
    ast.IsNot: 'is not',
    ast.In: 'in',
    ast.NotIn: 'not in',
}

class ExpressionParser(ast.NodeVisitor):
    """
    Parses a given expression string to extract operators (function names,
    arithmetic, and comparison operators) and datafields (variables that
    are used but not defined within the expression).
    """

    def __init__(self):
        self.operators = set()
        self.all_names = set()
        self.defined_variables = set()

    def visit_Call(self, node):
        """
        Visits a Call node in the AST. This represents a function call.
        The function's name is considered an operator.
        """
        if isinstance(node.func, ast.Name):
            self.operators.add(node.func.id)
        # Ensure we visit the arguments of the call
        self.generic_visit(node)

    def visit_BinOp(self, node):
        """
        Visits a BinOp node in the AST. This represents a binary operation
        (e.g., +, -, *, /). The operator symbol is extracted.
        """
        op_type = type(node.op)
        if op_type in OPERATOR_MAP:
            self.operators.add(OPERATOR_MAP[op_type])
        self.generic_visit(node)

    def visit_Compare(self, node):
        """
        Visits a Compare node in the AST. This represents a comparison operation
        (e.g., ==, !=, <, >). All comparison operators are extracted.
        """
        for op in node.ops:
            op_type = type(op)
            if op_type in OPERATOR_MAP:
                self.operators.add(OPERATOR_MAP[op_type])
        self.generic_visit(node)

    def visit_Name(self, node):
        """
        Visits a Name node. This represents a variable or a function name.
        We add all encountered names to a set for later filtering.
        """
        self.all_names.add(node.id)

    def visit_Assign(self, node):
        """
        Visits an Assign node. This represents a variable assignment.
        We track which variables are defined within the expression.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_variables.add(target.id)
        # Visit the right-hand side of the assignment
        self.generic_visit(node)

    def parse(self, expression_string: str) -> tuple[list[str], list[str]]:
        """
        Parses the expression string.

        Args:
            expression_string: The string containing the expression(s).

        Returns:
            A tuple containing two lists: sorted operators and sorted datafields.
        """
        # 1. Clean up the string: remove comments and handle semicolons
        cleaned_expr = expression_string.split('-->')[0]
        statements = [stmt.strip() for stmt in cleaned_expr.split(';')]
        python_code = '\n'.join(filter(None, statements))

        # 2. Parse the string into an Abstract Syntax Tree
        try:
            tree = ast.parse(python_code)
        except SyntaxError as e:
            print(f"Error parsing expression: {e}")
            return [], []

        # 3. Reset state and walk the tree
        self._reset_state()
        self.visit(tree)

        # 4. Determine datafields: they are names that are used but never
        #    assigned to and are not operators themselves.
        datafields = self.all_names - self.defined_variables - self.operators
        
        return sorted(list(self.operators)), sorted(list(datafields))

    def _reset_state(self):
        """Resets the internal state for a new parsing operation."""
        self.operators = set()
        self.all_names = set()
        self.defined_variables = set()


def main():
    """
    Demonstrates the usage of the ExpressionParser with example expressions.
    """
    # Original example
    expression1 = "a = ts_mean(close, 20); b = ts_corr(open, close, 20); sigmoid(a * b)"
    parser = ExpressionParser()
    operators1, datafields1 = parser.parse(expression1)
    
    print("Parsing Expression 1:")
    print(f"  '{expression1}'")
    print("-" * 20)
    print(f"Detected Operators: {operators1}")
    print(f"Detected Datafields: {datafields1}")
    print("\n" + "="*50 + "\n")

    # New example with arithmetic and comparison operators
    expression2 = "x = (high + low) / 2; y = x * 1.5; result = ts_sum(y, 10) > 100 and close < open"
    operators2, datafields2 = parser.parse(expression2)

    print("Parsing Expression 2:")
    print(f"  '{expression2}'")
    print("-" * 20)
    print(f"Detected Operators: {operators2}")
    print(f"Detected Datafields: {datafields2}")
    print("\n" + "="*50 + "\n")

    expression3 = "z = func(a == b and c != d)"
    operators3, datafields3 = parser.parse(expression3)

    print("Parsing Expression 3:")
    print(f"  '{expression3}'")
    print("-" * 20)
    print(f"Detected Operators: {operators3}")
    print(f"Detected Datafields: {datafields3}")


if __name__ == "__main__":
    main()
