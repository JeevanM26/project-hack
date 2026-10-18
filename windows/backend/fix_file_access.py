# filename: fix_file_access.py

# Complete runnable code
import os

def access_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return None

# Sample test calls
file_path = os.path.join(os.getcwd(), "solution.py")
file_content = access_file(file_path)
print(f"File content: {file_content}")