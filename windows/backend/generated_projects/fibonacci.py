# filename: fibonacci.py

def fibonacci(n):
    """
    Calculates the nth Fibonacci number.

    Args:
        n (int): The index of the Fibonacci number to calculate.

    Returns:
        int: The nth Fibonacci number.
    """

    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)


# Sample test calls
print(fibonacci(5))
print(fibonacci(10))