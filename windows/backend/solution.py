# filename: solution.py

# Define the target directory
target_directory = "."

# Define the source and target file paths
source_file_path = "input_data.txt"
target_file_path = "output_data.txt"

# Open the source and target files for reading
with open(source_file_path, "r") as source_file, open(target_file_path, "w") as target_file:
    # Read the contents of the source file
    source_contents = source_file.read()

    # Write the contents of the source file to the target file
    target_file.write(source_contents)

# Print a message to the console
print("Data successfully swapped!")