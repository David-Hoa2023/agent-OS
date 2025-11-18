"""Mathematical calculation tool."""


class Calculator:
    """Safe mathematical expression evaluator."""

    def calculate(self, expression: str) -> float:
        """
        Evaluate a mathematical expression.

        Args:
            expression: Math expression (e.g., "2 + 2 * 3")

        Returns:
            Result of calculation
        """
        try:
            # Safe eval for math only
            allowed_names = {
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'pow': pow
            }

            # Evaluate with restricted builtins
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)

        except SyntaxError:
            return "Error: Invalid expression syntax"
        except Exception as e:
            return f"Error: {str(e)}"
