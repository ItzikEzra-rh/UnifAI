from global_utils.config.config import SharedConfig
from typing import Any, Type
from pydantic import BaseModel
import json
import os
from pathlib import Path
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from jsonschema import validate, ValidationError, Draft202012Validator
from datamodel_code_generator import (
    generate,
    InputFileType,
    DataModelType,
    PythonVersion
)
import tempfile
import importlib.util
import sys
import re

config = SharedConfig()


def get_mongo_url():
    ip = config.mongodb_ip
    port = config.mongodb_port
    return f"mongodb://{ip}:{port}/"


def get_rabbitmq_url(user=None, password=None):
    ip = config.rabbitmq_ip
    port = config.rabbitmq_port

    if user and password:
        return f'amqp://{user}:{password}@{ip}:{port}'
    else:
        return f'amqp://{ip}:{port}'


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def sort_nested_dict(data):
    if isinstance(data, dict):
        return {key: sort_nested_dict(value) for key, value in sorted(data.items())}
    elif isinstance(data, list):
        return sorted(sort_nested_dict(x) for x in data)
    return data


def get_root_dir() -> Path:
    """
    Get the root directory of the project dynamically.

    Returns:
        Path: The root directory of the project.
    """
    # Resolve the directory containing this file
    current_file = Path(__file__).resolve()
    # Navigate up to the project root (adjust number of parents based on your structure)
    root_dir = current_file.parents[1]

    return root_dir


# Global persistent event loop thread for consistent async execution
_PERSISTENT_LOOP = None
_PERSISTENT_THREAD = None
_LOOP_LOCK = threading.Lock()


def _get_persistent_loop():
    """Get or create a persistent event loop running in a dedicated thread."""
    global _PERSISTENT_LOOP, _PERSISTENT_THREAD

    if _PERSISTENT_LOOP is None or _PERSISTENT_LOOP.is_closed():
        with _LOOP_LOCK:
            if _PERSISTENT_LOOP is None or _PERSISTENT_LOOP.is_closed():
                # Create a new event loop in a dedicated thread
                loop_ready = threading.Event()

                def run_event_loop():
                    global _PERSISTENT_LOOP
                    _PERSISTENT_LOOP = asyncio.new_event_loop()
                    asyncio.set_event_loop(_PERSISTENT_LOOP)
                    loop_ready.set()
                    _PERSISTENT_LOOP.run_forever()

                _PERSISTENT_THREAD = threading.Thread(target=run_event_loop, daemon=True)
                _PERSISTENT_THREAD.start()
                loop_ready.wait()  # Wait for loop to be ready

    return _PERSISTENT_LOOP


def run_async(awaitable: Any) -> Any:
    """
    Always run awaitable in the same persistent event loop for consistency.
    
    This ensures all async operations (including McpServerClient locks) 
    happen in the same event loop, preventing "bound to different event loop" errors.
    
    Handles both cases:
    1. No event loop running (main thread) 
    2. Event loop already running (nested call from async context)
    
    In both cases, we use the persistent loop for consistency.
    """
    # Always use persistent loop regardless of current context
    persistent_loop = _get_persistent_loop()
    future = asyncio.run_coroutine_threadsafe(awaitable, persistent_loop)
    return future.result()


def json_schema_model(
        schema: dict,
        model_name: str
) -> Type[BaseModel]:
    """
    Generate and load a Pydantic model class from a given JSON Schema.

    Args:
        schema (dict): The JSON schema dict to convert into a model.
        model_name (str): The name of the model class to retrieve after generation.

    Returns:
        Type[BaseModel]: The generated Pydantic model class.

    Raises:
        AttributeError: If the specified model class is not found.
    """
    model_name = to_pascal_case(model_name)
    schema_str = json.dumps(schema)

    with tempfile.TemporaryDirectory() as temp_dir:
        module_name = "_generated_model"
        output_file = Path(temp_dir) / f"{module_name}.py"

        generate(
            input_=schema_str,
            input_file_type=InputFileType.JsonSchema,
            output_model_type=DataModelType.PydanticV2BaseModel,
            target_python_version=PythonVersion.PY_310,
            use_annotated=False,
            field_constraints=True,
            use_field_description=True,
            reuse_model=True,
            use_title_as_name=False,
            use_standard_collections=True,
            use_union_operator=True,
            strict_nullable=True,
            keep_model_order=True,
            output=output_file
        )

        sys.path.insert(0, temp_dir)
        try:
            # with open(output_file, "r") as f:
            #     print(f.read())
            spec = importlib.util.spec_from_file_location(module_name, str(output_file))
            if not spec or not spec.loader:
                raise ImportError(f"Could not create module spec for '{module_name}'")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            model_classes = [
                cls for cls in module.__dict__.values()
                if isinstance(cls, type) and issubclass(cls, BaseModel) and cls.__module__ == module_name
            ]

            if not model_classes:
                raise AttributeError("No Pydantic BaseModel subclass found in generated code.")

            model_cls = getattr(module, "Model", None)
            model_cls.model_rebuild(force=True, _types_namespace=module.__dict__)
            return model_cls
        finally:
            sys.path.remove(temp_dir)


def to_pascal_case(s: str) -> str:
    # Split on underscores, hyphens, and capital word boundaries
    words = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', re.sub(r'[-_]', ' ', s))
    return ''.join(word.capitalize() for word in words)


def validate_arguments(schema: dict, args: dict):
    try:
        # Validate the data against the JSON Schema
        validate(instance=args, schema=schema)
        return True
    except ValidationError as e:
        # Handle or raise
        raise ValueError(f"Validation error: {e.message}")
