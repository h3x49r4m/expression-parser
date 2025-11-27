====================================
Expression Parser
====================================

A Python project to parse and validate expressions. This tool provides a robust way to inspect expressions, extract their components, and validate them against a configurable set of rules.

The project uses Python's built-in ``ast`` (Abstract Syntax Tree) module to safely parse expression strings that follow Python-like syntax.

Key Components
--------------

1.  **ExpressionParser**: Parses a given expression string to extract operators (function names, arithmetic, and comparison operators) and datafields (variables that are used but not defined within the expression).

2.  **ExpressionValidator**: Validates an expression against a rich set of rules defined in external configuration files. This is the main feature of this project.

Features
--------

-   **Parsing**:
    -   Parses complex, multi-statement expressions.
    -   Identifies function calls, arithmetic operators, and comparison operators.
    -   Extracts source "datafields" used in the expressions.

-   **Validation**:
    -   **Configurable Rules**: Operator and datafield definitions are stored in ``_data/operators.json`` and ``_data/datafields.json``, allowing for easy modification without changing the code.
    -   **Operator Validation**: Checks if all operators in an expression are from the predefined set in ``operators.json``.
    -   **Datafield Validation**: Ensures all datafields are from the predefined set in ``datafields.json``.
    -   **Parameter Validation**:
        -   Checks the number of arguments for each function call.
        -   Validates keyword argument names.
        -   Validates the **type** of keyword arguments (e.g., `bool`, `int`, `float`, `str`).
        -   Validates numeric parameter values against **min/max ranges**.
        -   Validates parameter values against a list of **allowed options** (enums).
    -   **Datafield Type System**:
        -   Datafields are assigned a `type` (`MATRIX`, `VECTOR`, `GROUP`) in ``datafields.json``.
        -   Enforces rules based on datafield type, such as requiring `VECTOR` datafields to be used only within `vec_` functions.

-   No external library dependencies beyond standard Python.

Project Structure
-----------------

-   ``expression_parser.py``: Contains the `ExpressionParser` class.
-   ``expression_validator.py``: Contains the `ExpressionValidator` class and the main script execution logic.
-   ``common_operators.py``: A shared file for the `OPERATOR_MAP` used by both the parser and validator.
-   ``_data/``
    -   ``operators.json``: Defines all valid operators and their validation rules (arguments, types, ranges, allowed values).
    -   ``datafields.json``: Defines all valid datafields and their types (`MATRIX`, `VECTOR`, `GROUP`).

Usage
-----

### ExpressionParser

To use the parser, import the ``ExpressionParser`` class and call its ``parse`` method.

.. code-block:: python

    from expression_parser import ExpressionParser

    expression = "price_diff = close - open; is_bullish = price_diff > 0"
    parser = ExpressionParser()
    operators, datafields = parser.parse(expression)

    print(f"Operators: {operators}")
    print(f"Datafields: {datafields}")

### ExpressionValidator

The validator is designed to be run from the command line and uses the configuration files in the `_data/` directory.

To run the validation tests, execute the following command:

.. code-block:: bash

    python3 expression_validator.py

This will execute a series of predefined tests in the ``main`` function that demonstrate the various validation capabilities, such as checking for invalid operators, datafields, parameter types, and incorrect usage of `VECTOR` type datafields.

Configuration
-------------

The behavior of the ``ExpressionValidator`` is controlled by the JSON files in the `_data/` directory.

**_data/operators.json**

Defines the rules for each operator, including argument counts, keyword argument types, allowed values, and ranges.

*Example entry:*

.. code-block:: json

    {
        "hump": {
            "min_args": 1,
            "max_args": 1,
            "kwargs": {
                "hump": {
                    "type": "float",
                    "min_val": 0,
                    "max_val": 1
                }
            }
        },
        "ts_returns": {
            "min_args": 2,
            "max_args": 2,
            "kwargs": {
                "mode": {
                    "type": "int",
                    "allowed": [1, 2]
                }
            }
        }
    }


**_data/datafields.json**

Defines the available datafields and their types.

*Example entries:*

.. code-block:: json

    [
        {
            "id": "close",
            "type": "MATRIX"
        },
        {
            "id": "tgr_price",
            "type": "VECTOR"
        },
        {
            "id": "industry",
            "type": "GROUP"
        }
    ]

By modifying these files, you can customize the validation logic to fit different expression languages and requirements.
