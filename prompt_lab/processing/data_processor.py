import random
from llm_client.vllm import VLLMClient
from utils.tokenizer import TokenizerUtils


class DataProcessor:
    def __init__(self, io_repository, project_config, api_url, model_name,
                 max_context_length, max_generation_length, batch_size):
        self.io_repository = io_repository
        self.max_context_length = max_context_length
        self.max_generation_length = max_generation_length
        self.tokenizer = TokenizerUtils(model_name,
                                        max_context_length=self.max_context_length,
                                        max_generation_length=self.max_generation_length)
        self.batch_size = batch_size
        self.llm_client = VLLMClient(api_url, model_name, max_context_length)
        self.project_config = project_config
        self.processed_data = self.io_repository.load_processed_data()
        self.skipped_data = self.io_repository.load_skipped_data()
        self.current_index = self.io_repository.load_progress()

    def process_element(self, element_data):
        element_type = element_data.get("element_type")
        input_option_groups = self.project_config["element_templates"].get(element_type, {})
        system_message = self.project_config.get("system_message", "")

        batch_prompts = []
        metadata = []
        total_token_count = 0
        token_limit = self.tokenizer.get_toking_limit()

        for group_name, options in input_option_groups.items():
            for category, templates in options.items():
                context, input_text = self.generate_random_input(templates, **element_data)
                formatted_input = self.tokenizer.format_chat_prompt([
                    {"role": "system", "content": system_message},
                    {"role": "context", "content": context},
                    {"role": "user", "content": input_text}
                ])

                prompt_tokens = self.tokenizer.tokenize(formatted_input)

                print(
                    f"\nEvaluating element {element_type} {self.current_index + 1}: Group '{group_name}', Category '{category}'")
                print(f"Prompt token count: {prompt_tokens}")
                print(f"Current total token count in batch: {total_token_count}")

                # Skip if a single prompt exceeds the token limit
                if prompt_tokens > token_limit:
                    print(f"Skipping prompt: Exceeds individual token limit of {token_limit}")
                    self.skipped_data.append(element_data)
                    self.io_repository.save_skipped_data(self.skipped_data)
                    continue

                # Check if adding this prompt would exceed either the token limit or batch size
                if (total_token_count + prompt_tokens > token_limit) or (len(batch_prompts) >= self.batch_size):
                    print(f"Processing batch: Reached token limit or batch size")
                    self.process_batch(batch_prompts, metadata, self.max_generation_length)
                    batch_prompts = []
                    metadata = []
                    total_token_count = 0  # Reset token count for the new batch

                # Add the current prompt to the batch
                batch_prompts.append(formatted_input)
                total_token_count += prompt_tokens
                metadata.append({
                    "element_type": element_type,
                    "group": group_name,
                    "category": category,
                    "input_text": input_text,
                    "original_data": element_data
                })
                print(f"Added prompt to batch. New batch size: {len(batch_prompts)}")
                print(f"Updated total token count: {total_token_count}")

        # Process any remaining prompts in the batch
        if batch_prompts:
            print(f"Processing final batch for element '{element_type}' (Index {self.current_index + 1})")
            self.process_batch(batch_prompts, metadata, self.max_generation_length)

        self.current_index += 1
        self.save_progress()
        self.save_data()

    def process_batch(self, batch_prompts, metadata, max_generation_length):
        responses = self.llm_client.send_request(batch_prompts, max_tokens=max_generation_length)
        for meta, response_text in zip(metadata, responses):
            self.processed_data.append({
                "input": meta["input_text"],
                "output": response_text,
                "element_type": meta["element_type"],
                "group": meta["group"],
                "category": meta["category"],
                "original_data": meta["original_data"]
            })
            self.print_progress(meta["element_type"], meta["group"], meta["category"], response_text)

    def generate_random_input(self, templates, **kwargs):
        context_template = self.project_config.get("context_template", "")
        context = context_template.format(**kwargs)
        selected_template = random.choice(templates)
        input_text = selected_template.format(**kwargs)
        return context, input_text

    def save_data(self):
        self.io_repository.save_processed_data(self.processed_data)

    def save_progress(self):
        self.io_repository.save_progress(self.current_index)

    def process_all_elements(self):
        data = self.io_repository.load_data()
        while self.current_index < len(data):
            element = data[self.current_index]
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
