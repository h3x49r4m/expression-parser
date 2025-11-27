import ast
import json

from common_operators import OPERATOR_MAP


class ExpressionValidator(ast.NodeVisitor):
    """
    Validates an expression string against a set of predefined operators
    and datafields, including operator parameters and their values.
    """

    def __init__(self, operators, datafields_config):
        self.operators = operators
        self.datafield_types = {df['id']: df['type'] for df in datafields_config}
        #self.datafields = set(self.datafield_types.keys())
        self.datafields = [df['id'] for df in datafields_config]
        self.errors = []
        self.defined_variables = set()
        self.function_calls = set()

    def validate(self, expression_string: str, separator=';') -> list[str]:
        """
        Validates the expression string.

        Args:
            expression_string: The string containing the expression(s).
            separator: The separator for multiple statements.

        Returns:
            A list of error messages. An empty list means the expression is valid.
        """
        self.errors = []
        self.defined_variables = set()
        self.function_calls = set()

        cleaned_expr = expression_string.strip()
        if not cleaned_expr:
            return []
            
        statements = [stmt.strip() for stmt in cleaned_expr.split(separator)]
        python_code = '\n'.join(filter(None, statements))

        try:
            tree = ast.parse(python_code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return self.errors

        # First pass to find all defined variables and function calls and add parent pointers
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.defined_variables.add(target.id)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.function_calls.add(node.func.id)

        # Second pass to validate the tree
        self.visit(tree)
        return self.errors

    def _validate_literal_kwarg(self, kw_name, value_node, kw_def, func_name, lineno):
        """
        Helper to validate the type and value of a literal keyword argument.
        """
        actual_value = None
        is_literal = False

        if isinstance(value_node, ast.Constant):  # Python 3.8+
            actual_value = value_node.value
            is_literal = True
        elif hasattr(ast, 'NameConstant') and isinstance(value_node, ast.NameConstant):  # Python < 3.8 for True, False, None
            actual_value = value_node.value
            is_literal = True
        elif hasattr(ast, 'Num') and isinstance(value_node, ast.Num):  # Python < 3.8 for numbers
            actual_value = value_node.n
            is_literal = True
        elif hasattr(ast, 'Str') and isinstance(value_node, ast.Str):  # Python < 3.8 for strings
            actual_value = value_node.s
            is_literal = True

        if not is_literal:
            # For positional arguments that are not literals, we can still do a basic check
            if isinstance(value_node, ast.Name) and value_node.id in self.datafields:
                 # It's a datafield, we assume it has the correct type at runtime
                 pass
            return 

        # Type validation
        expected_type = kw_def.get('type')
        if expected_type and expected_type != 'any':
            type_ok = False
            if expected_type == 'bool' and isinstance(actual_value, bool):
                type_ok = True
            elif expected_type == 'int' and isinstance(actual_value, int) and not isinstance(actual_value, bool):
                type_ok = True
            elif expected_type == 'float' and isinstance(actual_value, float):
                type_ok = True
            elif expected_type == 'number' and isinstance(actual_value, (int, float)) and not isinstance(actual_value, bool):
                type_ok = True
            elif expected_type == 'str' and isinstance(actual_value, str):
                type_ok = True
            
            if not type_ok:
                self.errors.append(f"Error at line {lineno}: Invalid type for keyword argument '{kw_name}' in '{func_name}'. Expected a {expected_type}, but got value '{actual_value}' of type {type(actual_value).__name__}.")
                return

        # Allowed values validation
        allowed_values = kw_def.get('allowed')
        if allowed_values and actual_value not in allowed_values:
            self.errors.append(f"Error at line {lineno}: Invalid value for keyword argument '{kw_name}' in '{func_name}'. Got '{actual_value}', but expected one of {allowed_values}.")
            return

        # Range validation
        if isinstance(actual_value, (int, float)):
            min_val = kw_def.get('min_val')
            max_val = kw_def.get('max_val')
            min_inclusive = kw_def.get('min_inclusive', True)
            max_inclusive = kw_def.get('max_inclusive', True)

            if min_val is not None and (actual_value < min_val if min_inclusive else actual_value <= min_val):
                op = ">=" if min_inclusive else ">"
                self.errors.append(f"Error at line {lineno}: Value for '{kw_name}' in '{func_name}' must be {op} {min_val}.")
            
            if max_val is not None and (actual_value > max_val if max_inclusive else actual_value >= max_val):
                op = "<=" if max_inclusive else "<"
                self.errors.append(f"Error at line {lineno}: Value for '{kw_name}' in '{func_name}' must be {op} {max_val}.")


    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            self.generic_visit(node)
            return

        func_name = node.func.id
        if func_name not in self.operators:
            self.errors.append(f"Error at line {node.lineno}: Operator '{func_name}' is not defined or allowed.")
            self.generic_visit(node)
            return
        
        op_def = self.operators[func_name]
        
        num_args = len(node.args)
        min_args = op_def.get('min_args', 0)
        max_args = float('inf') if op_def.get('max_args', -1) == -1 else op_def.get('max_args', 0)

        if num_args < min_args:
            self.errors.append(f"Error at line {node.lineno}: '{func_name}' expects at least {min_args} positional arguments, but got {num_args}.")
        if num_args > max_args:
            self.errors.append(f"Error at line {node.lineno}: '{func_name}' expects at most {op_def.get('max_args')} positional arguments, but got {num_args}.")

        # Positional argument type validation for 'd' parameters
        for i, arg_node in enumerate(node.args):
            # A simple heuristic to check if the argument is a 'days' parameter
            if func_name.startswith('ts_') and len(node.args) > i and (op_def.get('min_args') > i) :
                 if isinstance(arg_node, ast.Constant) and not isinstance(arg_node.value, int):
                     self.errors.append(f"Error at line {node.lineno}: The 'days' parameter in '{func_name}' must be an integer, not a {type(arg_node.value).__name__}.")

        valid_kwarg_defs = op_def.get('kwargs', {})
        for keyword in node.keywords:
            kw_name = keyword.arg
            if kw_name not in valid_kwarg_defs:
                self.errors.append(f"Error at line {node.lineno}: Invalid keyword argument '{kw_name}' for function '{func_name}'.")
                continue

            kw_def = valid_kwarg_defs[kw_name]
            self._validate_literal_kwarg(kw_name, keyword.value, kw_def, func_name, node.lineno)
            
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.function_calls:
            return

        if isinstance(node.ctx, ast.Load):
            is_defined_var = node.id in self.defined_variables
            is_datafield = node.id in self.datafields
            is_operator = node.id in self.operators

            if not is_defined_var and not is_datafield and not is_operator:
                self.errors.append(f"Error at line {node.lineno}: Datafield or variable '{node.id}' is not defined or allowed.")
                return

            if is_datafield and self.datafield_types.get(node.id) == 'VECTOR':
                parent = getattr(node, 'parent', None)
                is_in_vec_op = False
                if parent and isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name):
                    if parent.func.id.startswith('vec_'):
                        is_in_vec_op = True
                
                if not is_in_vec_op:
                    self.errors.append(f"Error at line {node.lineno}: Datafield '{node.id}' of type VECTOR must be used inside a 'vec_' operator.")
        
    def visit_BinOp(self, node):
        op_symbol = OPERATOR_MAP.get(type(node.op))
        if op_symbol not in self.operators:
            self.errors.append(f"Error at line {node.lineno}: Operator '{op_symbol}' is not allowed.")
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            op_symbol = OPERATOR_MAP.get(type(op))
            if op_symbol not in self.operators:
                self.errors.append(f"Error at line {node.lineno}: Operator '{op_symbol}' is not allowed.")
        self.generic_visit(node)
        
    def visit_BoolOp(self, node):
        op_name = 'and' if isinstance(node.op, ast.And) else 'or'
        if op_name not in self.operators:
            self.errors.append(f"Error at line {node.lineno}: Operator '{op_name}' is not allowed.")
        else:
            op_def = self.operators[op_name]
            num_args = len(node.values)
            min_args = op_def.get('min_args', 0)
            max_args = float('inf') if op_def.get('max_args', -1) == -1 else op_def.get('max_args', 0)

            if num_args < min_args:
                self.errors.append(f"Error at line {node.lineno}: '{op_name}' expects at least {min_args} operands, but got {num_args}.")
            if num_args > max_args:
                self.errors.append(f"Error at line {node.lineno}: '{op_name}' expects at most {op_def.get('max_args')} operands, but got {num_args}.")
                
        self.generic_visit(node)


def main():
    """
    Demonstrates the usage of the ExpressionValidator.
    """
    with open('_data/operators.json', 'r') as f:
        predefined_operators = json.load(f)
    
    with open('_data/datafields.json', 'r') as f:
        predefined_datafields_config = json.load(f)

    validator = ExpressionValidator(predefined_operators, predefined_datafields_config)

    print("--- Running Validation Tests ---")

    test_expressions = {
        "Valid VECTOR usage": "vec_avg(tgr_price)",
        "Invalid VECTOR usage": "ts_mean(tgr_price, 10)",
        "Invalid operator": "a = ts_std(close, 20)",
        "Invalid datafield": "ts_mean(abc, 20)",
        "Invalid arg count": "ts_mean(close)",
        "Invalid keyword arg name": "ts_mean(close, 20, invalid_kw=1)",
        "Invalid keyword arg type": "normalize(x, useStd=0.4)",
        "Invalid keyword arg value": "ts_returns(close, 10, mode=3)",
        "Invalid range for hump": "hump(x, hump=1.2)",
        "Invalid enum for quantile": "quantile(x, driver='abc')",
        "Invalid 'days' parameter (float)": "ts_mean(close, 20.5)",
        "Valid 'days' parameter (int)": "ts_mean(close, 20)",
        "Valid group_mean parameter": "gmean = group_mean(x, close, industry); gmean = ts_delay(gmean, 20)",
        "Invalid op name": "ts_tex(x, 1)"
    }

    for description, expression in test_expressions.items():
        print(f"\nValidating ({description}): '{expression}'")
        errors = validator.validate(expression)
        if not errors:
            print("Result: Expression is valid.")
        else:
            print("Result: Validation errors found:")
            for error in errors:
                print(f"  - {error}")


if __name__ == "__main__":
    main()
