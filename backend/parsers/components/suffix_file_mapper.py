import os
import json
from components.robot_parser import RobotParser

def find_files_with_suffixes(directory, suffixes):
    """
    Recursively searches for files ending with any of the provided suffixes in the given directory and its subdirectories.
    Returns a dictionary where the keys are the relative file paths without the suffix extension and the values are the file contents.
    """
    files_content = {}

    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(suffix) for suffix in suffixes):
                # Get the relative path to the file from the base directory
                relative_path = os.path.relpath(os.path.join(root, file), directory)

                # Remove the suffix extension
                # relative_path_without_ext = os.path.splitext(relative_path)[0]

                # Read the file content
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                robot_parser = RobotParser(file_path=file_path)
                files_settings = robot_parser.setting_parser()

                # Store the relative path and content in the dictionary
                files_content[relative_path] = {
                    "settings": files_settings, 
                    "content": file_content,
                }

    return files_content

def write_to_file(my_list, filename="default.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

def main():
    # Define the directory to search
    directory_to_search = "/home/cloud-user/Projects/ods-ci"  # Replace with your directory path
    suffixes = [".robot", ".resource"]  # List of suffixes to search for
    project_name = "RHOAI"

   # Get the dictionary of files that end with any of the specified suffixes and their contents
    files = find_files_with_suffixes(directory_to_search, suffixes)

    # Output the result
    for file_name, file_attr in files.items():
        file_settings = file_attr.get("settings")
        file_content = file_attr.get("content")
        print(f"File Name: {file_name}\nSettings:\n{file_settings}\nContent:\n{file_content}\n{'-'*40}")

    write_to_file(json.dumps(files), filename=f'{project_name}_tests_mapping.txt')

if __name__ == "__main__":
    main()