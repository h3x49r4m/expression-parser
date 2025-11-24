===============
Expression Parser
===============

A simple, generic expression parser in Python designed to extract operators and datafields from a given string of expressions.

The script uses Python's built-in ``ast`` (Abstract Syntax Tree) module to safely and robustly parse expression strings that resemble Python syntax.

Features
--------

- Parses complex, multi-statement expressions separated by semicolons.
- Identifies function calls (e.g., ``ts_mean``, ``sigmoid``) as operators.
- Identifies a wide range of arithmetic (``+``, ``-``, ``*``, ``/``) and comparison (``>``, ``<``, ``==``, etc.) operators.
- Extracts "datafields," which are source variables that are used in the expression but not defined within it.
- No external library dependencies.

Usage
-----

To use the parser in your own project, import the ``ExpressionParser`` class from the ``expression_parser.py`` file and call the ``parse`` method.

.. code-block:: python

    from expression_parser import ExpressionParser

    # Your expression string
    expression = "price_diff = close - open; is_bullish = price_diff > 0"

    # Create a parser instance
    parser = ExpressionParser()

    # Parse the expression
    operators, datafields = parser.parse(expression)

    # Print the results
    print(f"Operators: {operators}")
    print(f"Datafields: {datafields}")

Expected Output:

.. code-block:: text

    Operators: ['-', '>']
    Datafields: ['close', 'open']


Running the Demo
----------------

The ``expression_parser.py`` script includes a ``main`` function that demonstrates its functionality with several predefined example expressions.

To run the demo, execute the following command in your terminal:

.. code-block:: bash

    python3 expression_parser.py

This will parse the examples and print the detected operators and datafields for each, showcasing the parser's capabilities.
