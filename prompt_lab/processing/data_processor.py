import random
from processing.llm_requester import LLMRequester


class DataProcessor:
    def __init__(self, input_repository, output_repository, tokenizer, project_config, api_url, max_context_length):
        self.input_repository = input_repository
        self.output_repository = output_repository
        self.tokenizer = tokenizer
        self.llm_requester = LLMRequester(api_url, max_context_length)
        self.project_config = project_config
        self.processed_data = []
        self.current_index = self.output_repository.load_progress()

    def process_element(self, element_data):
        element_type = element_data.get("element_type")
        input_option_groups = self.project_config["element_templates"].get(element_type, {})

        for group_name, options in input_option_groups.items():
            for category, templates in options.items():
                context, input_text = self.generate_random_input(templates, **element_data)
                formatted_input = self.llm_requester.prompt_format(context, input_text)
                if self.tokenizer.is_within_limit(formatted_input):
                    response = self.llm_requester.send_request(formatted_input)
                    output = self.llm_requester.extract_assistant_text(response.text)
                    self.processed_data.append({
                        "input": input_text,
                        "output": output,
                        "element_type": element_type,
                        "group": group_name,
                        "category": category,
                        "original_data": element_data
                    })
                    # Print the current progress and output
                    self.print_progress(element_type, group_name, category, output)

        # Increment and save progress after processing each element
        self.current_index += 1
        self.save_progress()
        self.save_data()

    def generate_random_input(self, templates, **kwargs):
        context_template = self.project_config.get("context_template", "")
        context = context_template.format(**kwargs)

        selected_template = random.choice(templates)
        input_text = selected_template.format(**kwargs)

        return context, input_text

    def save_data(self):
        self.output_repository.save_processed_data(self.processed_data)

    def save_progress(self):
        self.output_repository.save_progress(self.current_index)  # Save progress based on current index

    def process_all_elements(self):
        data = self.input_repository.load_data()
        for element in data[self.current_index:]:
            self.process_element(element)

    def print_progress(self, element_type, group_name, category, output):
        """Prints the progress of the current processing element in a stylized format."""
        separator = "=" * 80
        print(separator)
        print(f"Processing Element {self.current_index + 1}".center(80))
        print(f"Element Type: {element_type} | Group: {group_name} | Category: {category}".center(80))
        print(separator)
        print(f"\n{output}\n")
        print(separator)
