import json
from unsloth import FastLanguageModel
from transformers import TextStreamer, TextIteratorStreamer

# Initialize the model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    max_seq_length=32768,
    dtype=None,
    load_in_4bit=True,
)

input_file = "/home/instruct/ncs_412_full_tests.json"  # Replace with your actual input file path

res = []
with open(input_file, 'r') as infile:
    data = json.load(infile)

    for elem in data:
        # Tokenize the text
        inputs = tokenizer([elem['test']], return_tensors="pt").to("cuda")
        token_ids = inputs['input_ids']

        # Calculate the number of tokens
        num_tokens = token_ids.size(1)

        # Filter elements based on the token count
        if num_tokens > 32768:
            print(f"Number of tokens: {num_tokens}")
            print("bigger than 32768")
            continue
        res.append(elem)

# Write the filtered results back to the file
with open(input_file, 'w') as outfile:
    json.dump(res, outfile, indent=4)  # Use indent for pretty-printing
