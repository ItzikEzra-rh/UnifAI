import json

def get_extensions_json(config_path="config/extensions.json"):
    """Fetch the list of extensions from a JSON config file."""
    try:
        with open(config_path, "r") as file:
            data = json.load(file)
        return {
            "frameworks": data.get("frameworks", []),
            "extensions": data.get("extensions", {})
        }    
    except FileNotFoundError:
        return {"error": "Config file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except Exception as e:
        return {"error": str(e)}
