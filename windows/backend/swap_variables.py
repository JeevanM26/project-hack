# filename: swap_variables.py

# Complete runnable code here

def swap_variables(a, b):
    # Get the current working directory
    cwd = os.getcwd()

    # Define the source and destination files
    source_file = os.path.join(cwd, "source.txt")
    destination_file = os.path.join(cwd, "target.txt")

    # Open the source and destination files for reading
    with open(source_file, "r") as source_file, open(destination_file, "w") as destination_file:
        # Read the contents of the source file
        source_content = source_file.read()

        # Swap the variables in the source file
        source_content = source_content.replace("variable1", str(a))
        source_content = source_content.replace("variable2", str(b))

        # Write the modified content back to the destination file
        destination_file.write(source_content)

# Sample test calls
a = 10
b = 20

swap_variables(a, b)

print("Variables swapped successfully!")