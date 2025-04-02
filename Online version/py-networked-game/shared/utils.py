def serialize_data(data):
    import json
    return json.dumps(data)

def deserialize_data(data):
    import json
    return json.loads(data)

def create_response(success, message, data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }

def validate_player_name(name):
    return isinstance(name, str) and len(name) > 0

def generate_unique_id(existing_ids):
    import uuid
    new_id = str(uuid.uuid4())
    while new_id in existing_ids:
        new_id = str(uuid.uuid4())
    return new_id