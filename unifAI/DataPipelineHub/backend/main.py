from shared import logger
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_thread_retriever import SlackThreadRetriever
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory

def slack_flow():
    """Example usage of the Slack pipeline components."""
    # Create configuration manager
    config_manager = SlackConfigManager()
    
    # Set up a project with tokens (in real usage, load from environment or secure storage)
    config_manager.set_project_tokens(
        project_id="example-project",
        bot_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb",
        user_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb"
    )
    
    config_manager.set_default_project("example-project")
    
    # Create a connector
    try:
        connector = SlackConnector(config_manager)
        
        # Test authentication
        if connector.authenticate():
            # Get available channels
            channels = connector.get_available_slack_channels(types="private_channel")
            print(f"Found {len(channels)} channels")
            
            # Get history for the first channel if available
            if channels:
                first_channel = channels[0]
                print(f"Getting messages for channel: {first_channel['channel_name']}")
                messages, thread_messages = connector.get_conversations_history(first_channel['channel_id'])
                print(f"Retrieved {len(messages)} messages")
                print(f"Retrieved {len(thread_messages)} thread_messages")
            
                # Initialize and use processor
                processor = SlackProcessor()

                processed_data = processor.process(messages, channel_name=first_channel['channel_name'])

                # Reset and chunk threads
                # chunker = SlackChunkerStrategy()
                # messages_chunks = chunker.chunk_content(processed_data)
                # print(f"Generated {len(messages_chunks)} chunks from messages")

                # Display results
                # for msg in processed_data:
                #     print(f"User: {msg['user']}, Message: {msg['text']}")

                # processed_thread_data = []
                # for msg in thread_messages:
                #     processed_single_thread_data = processor.process(msg, channel_name="random")
                #     processed_thread_data.append(processed_single_thread_data)

                # # Initialize chunker
                # chunker = SlackChunkerStrategy(
                #     max_tokens_per_chunk=500,
                #     overlap_tokens=50,
                #     time_window_seconds=300
                # )
                
                # # Reset and chunk threads
                # chunker = SlackChunkerStrategy()
                # thread_chunks = chunker.chunk_content(processed_thread_data)
                # print(f"Generated {len(thread_chunks)} chunks from threads")

                # # Display results
                # # for sample_thread in thread_chunks:
                # #     print(sample_thread)

                # # Create embedding generator
                # embedding_config = {
                #     "type": "sentence_transformer",
                #     "model_name": "all-MiniLM-L6-v2",
                #     "batch_size": 32
                # }
                
                # embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
                
                # # Generate embeddings
                # enriched_chunks = embedding_generator.generate_embeddings(thread_chunks)
                
                # # Create vector storage
                # storage_config = {
                #     "type": "qdrant",
                #     "collection_name": "slack_data",
                #     "embedding_dim": embedding_generator.embedding_dim,
                #     "url": "http://localhost",
                #     "port": 6333
                # }
                
                # vector_storage = VectorStorageFactory.create(storage_config)
                
                # # Initialize storage
                # vector_storage.initialize()
                
                # # Store embeddings
                # vector_storage.store_embeddings(enriched_chunks)
                
    except Exception as e:
        logger.error(f"Error in slack_flow: {str(e)}")

def slack_chunker():
    # Sample individual messages
    sample_messages = [
        {
            "time_stamp": "1609459200.000700",
            "user": "U012A3CDE",
            "text": "Has anyone looked at the latest revenue numbers?",
            "metadata": {
                "channel_name": "finance"
            }
        },
        {
            "time_stamp": "1609459230.000800",  # 30 seconds later
            "user": "U012A3CDF",
            "text": "Yes, they're looking good for Q3!",
            "metadata": {
                "channel_name": "finance"
            }
        },
        {
            "time_stamp": "1609459500.000900",  # 5 minutes later
            "user": "U012A3CDG",
            "text": "What's on the agenda for today's meeting?",
            "metadata": {
                "channel_name": "finance"
            }
        },
                {
            "time_stamp": "1609460500.000900",
            "user": "U028A3CDG",
            "text": "Hey, anyone is here? That's only a debug meesage, I expect it to be treated as single separated chunk",
            "metadata": {
                "channel_name": "finance"
            }
        }
    ]
    
    # Sample thread
    sample_thread = [
        [
            {
                "time_stamp": "1609460000.001000",
                "user": "U012A3CDE",
                "text": "Should we implement the new feature now or wait until next sprint?",
                "metadata": {
                    "channel_name": "engineering",
                    "thread_ts": "1609460000.001000"
                }
            },
            {
                "time_stamp": "1609460060.001100",
                "user": "U012A3CDF",
                "text": "I think we should wait, we have too many priorities this sprint already.",
                "metadata": {
                    "channel_name": "engineering",
                    "thread_ts": "1609460000.001000"
                }
            },
            {
                "time_stamp": "1609460120.001200",
                "user": "U012A3CDG",
                "text": "Agreed, let's put it in the backlog for next sprint planning.",
                "metadata": {
                    "channel_name": "engineering",
                    "thread_ts": "1609460000.001000"
                }
            }
        ]
    ]
    
    # Initialize chunker
    chunker = SlackChunkerStrategy(
        max_tokens_per_chunk=500,
        overlap_tokens=50,
        time_window_seconds=300
    )
    
    # Chunk individual messages
    message_chunks = chunker.chunk_content(sample_messages)
    print(f"Generated {len(message_chunks)} chunks from individual messages")
    
    # Reset and chunk threads
    chunker = SlackChunkerStrategy()
    thread_chunks = chunker.chunk_content(sample_thread)
    print(f"Generated {len(thread_chunks)} chunks from threads")

def embedding_flow():
    # Sample chunk
    sample_chunks = [
        {
            "text": "This is a sample Slack message about the project timeline.",
            "metadata": {
                "source_type": "slack_conversation",
                "channel_name": "project-updates",
                "time_range": "1609459200.000700-1609459230.000800",
                "message_count": 3
            }
        },
        {
            "text": "The new feature will be ready by next sprint according to the engineering team.",
            "metadata": {
                "source_type": "slack_thread",
                "channel_name": "engineering",
                "thread_id": "1609460000.001000",
                "time_range": "1609460000.001000-1609460120.001200",
                "message_count": 3
            }
        }
    ]
    
    # Create embedding generator
    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
    
    # Generate embeddings
    enriched_chunks = embedding_generator.generate_embeddings(sample_chunks)
    
    # Create vector storage
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data",
        "embedding_dim": embedding_generator.embedding_dim,
        "url": "http://localhost",
        "port": 6333
    }
    
    vector_storage = VectorStorageFactory.create(storage_config)
    
    # Initialize storage
    vector_storage.initialize()
    
    # Store embeddings
    vector_storage.store_embeddings(enriched_chunks)
    
    # Example search
    query = "When will the new feature be ready?"
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=2,
        filters={"metadata.channel_name": "engineering"}
    )
    
    print(f"Search results for: '{query}'")
    for result in search_results:
        print(f"Score: {result['score']:.4f}, Text: {result['text']}")

def rag_flow():
    # Create embedding generator
    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
    
    # Create vector storage
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data",
        "embedding_dim": embedding_generator.embedding_dim,
        "url": "http://localhost",
        "port": 6333
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    
    # Example search
    query = "What can you tell me about the Jira-summarizer?"
    # query = "Can you give me information about a message start with the text `The following is a DEBUG MESSAGE, please don't respond.`"
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=2,
        filters={"metadata.channel_name": "automation-and-tools-israel"}
    )
    
    print(f"Search results for: '{query}'")
    for result in search_results:
        print(f"Score: {result['score']:.4f}, Text: {result['text']}")

if __name__ == "__main__":
    # slack_flow()
    # slack_chunker()
    # embedding_flow()
    rag_flow()