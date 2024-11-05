from unsloth import FastLanguageModel
import torch
import os
import argparse
from trl import SFTTrainer
from transformers import TrainingArguments

dtype = None
load_in_4bit = True  # Use 4bit quantization to reduce memory usage. Can be False.

output_dir = ""


def find_latest_checkpoint(output_dir):
    # List all checkpoint directories
    checkpoints = [d for d in os.listdir(output_dir) if d.startswith('checkpoint-')]

    # If there are no checkpoints, return None
    if not checkpoints:
        return ""

    # Sort checkpoints by their number (assumes the format 'checkpoint-<number>')
    checkpoints = sorted(checkpoints, key=lambda x: int(x.split('-')[1]), reverse=True)

    # Return the path to the latest checkpoint
    return os.path.join(output_dir, checkpoints[0])


def get_model(max_seq_length=8192, model_name="llama-3-8b-Instruct-bnb-4bit", lora_rank=16):
    # Set the output directory where checkpoints are saved
    global output_dir

    # Find the latest checkpoint
    latest_checkpoint = find_latest_checkpoint(output_dir) if os.path.exists(output_dir) else ""
    if latest_checkpoint:
        print(f"latest checkpoint {latest_checkpoint} - continue training from this checkpoint")
    else:
        print("no checkpoint - new run")

    if os.path.exists(latest_checkpoint):
        model, tokenizer = FastLanguageModel.from_pretrained(latest_checkpoint)
    else:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
            # token = "hf_...", # use one if using gated models like meta-llama/Llama-2-7b-hf
        )

    # Initialize the LoRA model
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,  # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj", ],
        lora_alpha=lora_rank * 2,
        lora_dropout=0.1,  # Supports any, but = 0 is optimized
        bias="none",  # Supports any, but = "none" is optimized
        # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
        use_gradient_checkpointing="unsloth",  # True or "unsloth" for very long context
        random_state=3407,
        use_rslora=False,  # We support rank stabilized LoRA
        loftq_config=None,  # And LoftQ
    )
    return model, tokenizer, latest_checkpoint


def get_data_set(tokenizer, dataset_name=""):
    EOS_TOKEN = tokenizer.eos_token  # do not forget this part!

    def formatting_prompts_func(examples):
        _input = examples["input"]
        output = examples["output"]

        texts = []
        for _input, output in zip(_input, output):
            prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>{_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>{output}<|eot_id|>"
            prompt = prompt + EOS_TOKEN
            texts.append(prompt)

        return {"text": texts, }

    pass

    from datasets import load_dataset

    dataset = load_dataset(dataset_name,
                           split="train")

    dataset = dataset.map(formatting_prompts_func, batched=True, )
    return dataset


def get_trainer(model, tokenizer, dataset, batch_size=8, max_seq_length=8192, epoch=1, dataset_name=""):
    global output_dir

    training_args = TrainingArguments(
        run_name=f"robot-framework-test-{dataset_name}",
        # report_to="wandb",
        per_device_train_batch_size=int(int(batch_size) / 4),
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=epoch,
        learning_rate=1e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir=output_dir,
        save_steps=2546,  # Save checkpoint every 744 steps
        save_total_limit=int(epoch),  # Only keep the last checkpoint
        load_best_model_at_end=False,  # Optional: only if you want to load the best model
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,  # Increase number of processes if you have more CPU cores
        packing=False,  # Can make training 5x faster for short sequences.
        args=training_args,
    )
    return trainer


def run(DATASET_NAME, MAX_SEQ_LEN, EPOCHS_NUMBER, BATCH_SIZE, MODEL_NAME, lora_rank):
    global output_dir
    model, tokenizer, checkpoint_dir = get_model(max_seq_length=MAX_SEQ_LEN, model_name=MODEL_NAME, lora_rank=lora_rank)
    dataset = get_data_set(tokenizer=tokenizer, dataset_name=DATASET_NAME)
    trainer = get_trainer(model=model, tokenizer=tokenizer, dataset=dataset, batch_size=int(BATCH_SIZE),
                          max_seq_length=MAX_SEQ_LEN, epoch=int(EPOCHS_NUMBER), dataset_name=DATASET_NAME)

    gpu_stats = torch.cuda.get_device_properties(0)
    start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
    print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
    print(f"{start_gpu_memory} GB of memory reserved.")

    trainer_stats = trainer.train(resume_from_checkpoint=checkpoint_dir if os.path.exists(checkpoint_dir) else None)

    used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
    used_percentage = round(used_memory / max_memory * 100, 3)
    lora_percentage = round(used_memory_for_lora / max_memory * 100, 3)
    print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
    print(f"{round(trainer_stats.metrics['train_runtime'] / 60, 2)} minutes used for training.")
    print(f"Peak reserved memory = {used_memory} GB.")
    print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
    print(f"Peak reserved memory % of max memory = {used_percentage} %.")
    print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")

    model.save_pretrained(os.path.join(output_dir, "final_model"))  # Local saving


def main():
    global output_dir
    parser = argparse.ArgumentParser(description="Run training script with parameters.")
    parser.add_argument('--dataset', type=str, required=True, help='dataset name')
    parser.add_argument('--max_seq_len', type=int, required=True, help='Maximum sequence length')
    parser.add_argument('--epochs_number', type=int, required=True, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, required=True, help='Batch size')
    parser.add_argument('--model_name', type=str, required=True, help='Name of the model')
    parser.add_argument('--lora_rank', type=str, required=True, help='lora rank')
    parser.add_argument('--output_dir', type=str, required=True, help='output dir')

    args = parser.parse_args()

    DATASET_NAME = args.dataset
    MAX_SEQ_LEN = int(args.max_seq_len)
    EPOCHS_NUMBER = int(args.epochs_number)
    BATCH_SIZE = int(args.batch_size)
    MODEL_NAME = args.model_name
    LORA_RANK = int(args.lora_rank)
    output_dir = args.output_dir

    print(
        f"DATASET_NAME: {DATASET_NAME}, MAX_SEQ_LEN: {MAX_SEQ_LEN}, EPOCHS_NUMBER: {EPOCHS_NUMBER}, BATCH_SIZE: {BATCH_SIZE}, MODEL_NAME: {MODEL_NAME}, LORA RANK: {LORA_RANK}, output dir: {output_dir}")

    run(DATASET_NAME, MAX_SEQ_LEN, EPOCHS_NUMBER, BATCH_SIZE, MODEL_NAME, LORA_RANK)


if __name__ == '__main__':
    main()

#"/home/instruct/openshift-qe-checkpoints"