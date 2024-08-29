import os
import json

def find_go_files(directory):
    """
    Recursively searches for .go files in the given directory and its subdirectories.
    Returns a dictionary where the keys are file names without the .go extension and the values are the file contents.
    """
    go_files_content = {}

    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".go"):
                # Get the file name without the .go extension
                file_name_without_ext = os.path.splitext(file)[0]

                # Construct the full path to the file
                file_path = os.path.join(root, file)

                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                # Store the file name and content in the dictionary
                go_files_content[file_name_without_ext] = file_content

    return go_files_content

def write_to_file(my_list, filename="default.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

def main():
    # Define the directory to search
    directory_to_search = "/home/cloud-user/Projects/eco-gotests/tests"  # Replace with your directory path

    # Get the dictionary of .go files and their contents
    go_files = find_go_files(directory_to_search)

    # Output the result
    for file_name, content in go_files.items():
        print(f"File Name: {file_name}\nContent:\n{content}\n{'-'*40}")

    write_to_file(json.dumps(go_files), filename='GO_tests_mapping.txt')

if __name__ == "__main__":
    main()