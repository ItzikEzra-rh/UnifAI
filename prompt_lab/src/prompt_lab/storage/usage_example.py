from storage import (HybridHFMongoRepository,
                     HuggingFaceDataHandler,
                     MongoDataHandler,
                     HFExporter)


def main():
    # 1) Create input handler
    input_handler = HuggingFaceDataHandler(repo_id="username/demo_dataset", split="train")

    # 2) Mongo handlers
    processed_handler = MongoDataHandler(
        uri="mongodb://localhost:27017/",
        db_name="my_db",
        collection_name="processed_data"
    )
    skipped_handler = MongoDataHandler(
        uri="mongodb://localhost:27017/",
        db_name="my_db",
        collection_name="skipped_data"
    )
    progress_handler = MongoDataHandler(
        uri="mongodb://localhost:27017/",
        db_name="my_db",
        collection_name="progress_data"
    )

    # 3) Exporter
    exporter = HFExporter()

    # 4) Build the repository
    repo = HybridHFMongoRepository(
        input_handler=input_handler,
        processed_handler=processed_handler,
        skipped_handler=skipped_handler,
        progress_handler=progress_handler,
        exporter=exporter
    )

    # 5) Use the repository
    for record in repo.load_data():
        # ... do something ...
        repo.save_processed_data({"foo": "bar"})  # example

    # 6) Export processed data to HF
    repo.export_processed_data_to_huggingface(repo_id="username/processed_dataset", hf_token="YOUR_TOKEN")

    # 7) Cleanup
    repo.close()


if __name__ == "__main__":
    main()
