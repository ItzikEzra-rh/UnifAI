import json


# files = ["backend_processed_dataset.json", "agent_processed_dataset.json"]
#
# dataset = []
# for file in files:
#     with open(file, 'r') as f:
#         data = json.load(f)
#     for i in range(0, len(data), 3):
#         elem = data[i]
#         dep = '\n'.join(elem['output']['dependencies'])
#         code = f"{dep}\n\n{elem['output']['code']}"
#         file_location = elem['output']['file_location']
#         dataset.append({"code": f"{code}\n\nlocation: {file_location}"})
#
# with open("AIM_project_code_dataset.json", "w") as f:
#     json.dump(dataset, f)



def merge_json_files(file1, file2, output_file):
    # Load the first JSON file
    with open(file1, 'r', encoding='utf-8') as f1:
        data1 = json.load(f1)
        for elem in data1:
            elem["input"] = f"file location in AIM: {elem['input']}"
            elem["output"] = f"code:\n\n```python\n{elem['output']}"

    # Load the second JSON file
    with open(file2, 'r', encoding='utf-8') as f2:
        data2 = json.load(f2)

    # Combine the data (assuming both are lists)
    merged_data = data1 + data2

    # Save the merged data into a new JSON file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(merged_data, outfile, indent=4, ensure_ascii=False)

    print(f"Merged data saved to {output_file}")

if __name__ == "__main__":
    json_file2 = "AIM_project_dataset.json"  # Replace with your first JSON file path
    json_file1 = "project_dataset.json"  # Replace with your second JSON file path
    output_json_file = "merged_file.json"  # The output file path

    merge_json_files(json_file1, json_file2, output_json_file)