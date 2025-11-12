"""
Module for mathematical operations and utilities.
"""

def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using recursion.

    Args:
        n (int): The position in the Fibonacci sequence.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathHelper:
    """
    A helper class for basic mathematical operations with a base value.

    Attributes:
        base (int): The base value for arithmetic operations.
    
    Methods:
        add(x: int) -> int: Add the base to x.
        multiply(x: int) -> int: Multiply the base by x.
    """

    def __init__(self, base: int):
        """
        Initialize the MathHelper with a base value.

        Args:
            base (int): The base value for arithmetic operations.
        """
        self.base = base
    
    def add(self, x: int) -> int:
        """
        Add the base to x.

        Args:
            x (int): The number to add to the base.

        Returns:
            int: The result of adding the base and x.
        """
        return self.base + x
    
    def multiply(self, x: int) -> int:
        """
        Multiply the base by x.

        Args:
            x (int): The number to multiply with the base.

        Returns:
            int: The result of multiplying the base and x.
        """
        return self.base * x