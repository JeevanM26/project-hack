# filename: fibonacci.py

def fibonacci(n):
  """
  Calculates the nth Fibonacci number.

  Args:
    n: The index of the Fibonacci number to calculate.

  Returns:
    The nth Fibonacci number.
  """

  if n == 0:
    return 0
  elif n == 1:
    return 1
  else:
    return fibonacci(n-1) + fibonacci(n-2)


# Print the first 10 Fibonacci numbers.
for i in range(10):
  print(fibonacci(i))