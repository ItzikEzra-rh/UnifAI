import markdown_it
from markdown_it.token import Token
import json


def parse_markdown(file_path, max_level=3):
    # Read the Markdown file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Initialize Markdown parser
    md = markdown_it.MarkdownIt()

    # Parse Markdown into tokens
    tokens = md.parse(content)

    elements = []
    current_section = None

    for token in tokens:
        if token.type == "heading_open":
            # Start a new section for each heading
            level = int(token.tag[1])  # e.g., 'h1' -> 1, 'h2' -> 2

            if level > max_level and current_section:
                # Treat all levels below max_level as part of the current section
                continue

            if current_section:
                elements.append(current_section)

            current_section = {
                "title": "",
                "description": "",
                "element_type": "heading",
                "code": False  # Default to False; will update if code is found
            }
        elif token.type == "inline" and current_section:
            if not current_section["title"]:
                # Set the title of the section
                current_section["title"] = token.content.strip()
            else:
                # Append content to the description
                current_section["description"] += token.content.strip() + " "
        elif token.type == "fence" and current_section:
            # Add code examples into the description with proper formatting
            language = token.info.strip()
            code = token.content.strip()
            if language == "json":
                current_section["description"] += f"\n```json\n{code}\n```"
            elif language in {"yaml", "yml"}:
                current_section["description"] += f"\n```yaml\n{code}\n```"
            # Update the code key to True
            current_section["code"] = True

    # Append the last section if it exists
    if current_section:
        elements.append(current_section)

    return elements


def save_to_json(data, output_path):
    """Save parsed data to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # Path to the README file
    markdown_file = "specification.md"  # Change this to the correct path
    output_file = "parsed_specification.json"

    # Parse the Markdown file with max level
    parsed_elements = parse_markdown(markdown_file, max_level=10)

    # Save parsed elements to a JSON file
    save_to_json(parsed_elements, output_file)

    print(f"Parsed data saved to {output_file}")
