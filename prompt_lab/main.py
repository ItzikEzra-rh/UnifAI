from core.factory import DataProcessorFactory


# Main Processing Function
def main():
    # Configure repositories for input and output
    data_processor = DataProcessorFactory().create()
    # Start processing
    data_processor.process_all_elements()


if __name__ == "__main__":
    main()
