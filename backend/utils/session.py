import os
import json

def set_session_status(session_dir, status, extra=None):
    status_path = os.path.join(session_dir, 'status.json')
    data = {'status': status}
    if extra:
        data.update(extra)
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def get_session_status(session_dir):
    status_path = os.path.join(session_dir, 'status.json')
    if not os.path.exists(status_path):
        return {'status': 'not found'}
    with open(status_path, 'r', encoding='utf-8') as f:
        return json.load(f) 