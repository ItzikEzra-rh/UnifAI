import matplotlib.pyplot as plt
from collections import defaultdict
from transformers import AutoTokenizer
from datasets import load_dataset
from tqdm import tqdm

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")

def tokenize_length(text, tokenizer):
    """Get the token length of a given text using the provided tokenizer."""
    # Note: Ensure your tokenizer uses a method compatible with .encode
    tokens = tokenizer.encode(text, truncation=False)
    return len(tokens)

def analyze_context_lengths(
        dataset_name,
        dataset_split="train",
        input_key="input",
        output_key="output",
        bins=None,
        output_image="token_length_distribution.png"
):
    """
    Analyze the token length of concatenated 'input' and 'output' fields in a Hugging Face dataset.
    This version uses the tokenizer's apply_chat_template method to format the conversation.

    Args:
        dataset_name (str): Name of the Hugging Face dataset.
        dataset_split (str): Split of the dataset to analyze (default: 'train').
        input_key (str): Key for the user input field in the dataset.
        output_key (str): Key for the assistant output field in the dataset.
        bins (list[int]): Sorted list of upper boundaries for bins. For example,
                          [64, 128, 256, 512, 1024, 2048, 4096, 8192]
                          would create intervals [1-64, 65-128, 129-256, ..., 4097-8192, >8192].
        output_image (str): Path to save the histogram image.

    Returns:
        dict: A dictionary with percentage distributions and token statistics.
    """
    # Default bins if none are provided
    if bins is None:
        bins = [64, 128, 256, 512, 1024, 2048, 4096, 8192]

    # Load the dataset
    print(f"Loading dataset '{dataset_name}' split '{dataset_split}'...")
    dataset = load_dataset(dataset_name, split=dataset_split)

    total_elements = len(dataset)
    token_counts = []
    bucket_counts = defaultdict(int)

    print("Analyzing token lengths...")
    for element in tqdm(dataset, total=total_elements):
        user_text = element.get(input_key, "")
        assistant_text = element.get(output_key, "")

        # Prepare the messages in the expected format for apply_chat_template
        messages = [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text}
        ]

        # Use the tokenizer's method to apply the chat template
        combined_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        token_len = tokenize_length(combined_text, tokenizer)
        token_counts.append(token_len)

        # Determine the bucket for this token length
        prev_bound = 1
        placed = False
        for bin_threshold in bins:
            if token_len <= bin_threshold:
                bucket_name = f"{prev_bound}-{bin_threshold}"
                bucket_counts[bucket_name] += 1
                placed = True
                break
            prev_bound = bin_threshold + 1

        if not placed:
            bucket_counts[f">{bins[-1]}"] += 1

    def parse_bucket_name(name):
        if name.startswith(">"):
            lower = int(name[1:])
            return (lower, float('inf'))
        else:
            parts = name.split('-')
            return (int(parts[0]), int(parts[1]))

    # Sort buckets by numerical range
    sorted_buckets = sorted(bucket_counts.items(), key=lambda x: parse_bucket_name(x[0]))

    results = {
        "total_elements": total_elements,
        "buckets": {
            bucket: {
                "count": bucket_counts[bucket],
                "percentage": (bucket_counts[bucket] / total_elements) * 100
            }
            for bucket in bucket_counts
        },
        "token_statistics": {
            "max_tokens": max(token_counts),
            "min_tokens": min(token_counts),
            "average_tokens": sum(token_counts) / total_elements,
        },
        "raw_token_counts": token_counts,
    }

    # Create and save histogram
    plt.figure(figsize=(10, 6))
    plt.hist(token_counts, bins=30, edgecolor='black', alpha=0.7)
    plt.title("Token Length Distribution (Chat Format)")
    plt.xlabel("Token Length")
    plt.ylabel("Frequency")
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()
    plt.savefig(output_image)
    plt.close()
    print(f"Histogram saved as {output_image}")

    # Print summary table
    print("\nToken Length Distribution by Bins:")
    print(f"{'Bucket':<20} {'Count':>10} {'Percentage':>12}")
    print("-" * 45)
    for bucket, info in sorted(results["buckets"].items(), key=lambda x: parse_bucket_name(x[0])):
        print(f"{bucket:<20} {info['count']:>10} {info['percentage']:>11.2f}%")

    print("\nToken Statistics:")
    for stat, value in results["token_statistics"].items():
        print(f"{stat.capitalize()}: {value}")

    return results

# Example usage:
# Adjust the dataset name, split, and keys as needed
bins = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
dataset_name = "oodeh/MTA-project"  # Replace with your dataset
dataset_split = "train"
input_key = "input"
output_key = "output"

analysis_results = analyze_context_lengths(
    dataset_name,
    dataset_split=dataset_split,
    input_key=input_key,
    output_key=output_key,
    bins=bins
)
