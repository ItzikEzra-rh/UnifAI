import matplotlib.pyplot as plt
from collections import defaultdict
from transformers import AutoTokenizer
from datasets import load_dataset

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")


def tokenize_length(text):
    """Get the token length of a given text."""
    tokens = tokenizer.encode(text, truncation=False)
    return len(tokens)


def analyze_context_lengths(dataset_name, dataset_split="train", input_key="input", output_key="output", bins=None,
                            output_image="token_length_distribution.png"):
    """
    Analyze the token length of concatenated 'input' and 'output' fields in a Hugging Face dataset.

    Args:
        dataset_name (str): Name of the Hugging Face dataset.
        dataset_split (str): Split of the dataset to analyze (default: 'train').
        input_key (str): Key for the input field in the dataset.
        output_key (str): Key for the output field in the dataset.
        bins (list): List of context length thresholds (e.g., [500, 1000, 2000, 4000, 8000]).
        output_image (str): Path to save the histogram image.

    Returns:
        dict: A dictionary with percentage distributions and token statistics.
    """
    if bins is None:
        bins = [500, 1000, 2000, 4000, 8000]

    # Load the dataset
    dataset = load_dataset(dataset_name, split=dataset_split)

    # Initialize counters
    total_elements = len(dataset)
    token_counts = []
    bucket_counts = defaultdict(int)

    # Analyze each element
    for element in dataset:
        combined_text = element.get(input_key, "") + " " + element.get(output_key, "")
        token_len = tokenize_length(combined_text)
        token_counts.append(token_len)

        # Determine the bucket
        for bin_threshold in bins:
            if token_len <= bin_threshold:
                bucket_counts[bin_threshold] += 1
                break
        else:
            bucket_counts["greater_than_{}".format(bins[-1])] += 1

    # Calculate percentages
    percentages = {k: (v / total_elements) * 100 for k, v in bucket_counts.items()}

    # Summarize results
    results = {
        "total_elements": total_elements,
        "bucket_percentages": percentages,
        "token_statistics": {
            "max_tokens": max(token_counts),
            "min_tokens": min(token_counts),
            "average_tokens": sum(token_counts) / total_elements,
        },
        "raw_token_counts": token_counts,  # Optional for further processing
    }

    # Save the histogram
    plt.hist(token_counts, bins=20, edgecolor='black', alpha=0.7)
    plt.title("Token Length Distribution")
    plt.xlabel("Token Length")
    plt.ylabel("Frequency")
    plt.savefig(output_image)  # Save the plot as a PNG file
    plt.close()  # Close the plot to free resources

    print(f"Histogram saved as {output_image}")

    return results


# Define dataset parameters
dataset_name = "oodeh/eco-gotests"  # Replace with the Hugging Face dataset name
dataset_split = "train"  # Change if needed
input_key = "input"  # Replace with the actual input key in your dataset
output_key = "output"  # Replace with the actual output key in your dataset

# Analyze the data
analysis_results = analyze_context_lengths(dataset_name, dataset_split, input_key, output_key)

# Print summary
print("Total Elements:", analysis_results["total_elements"])
print("Token Length Buckets and Percentages:")
for bucket, percent in analysis_results["bucket_percentages"].items():
    print(f"  <= {bucket}: {percent:.2f}%")
print("\nToken Statistics:", analysis_results["token_statistics"])
