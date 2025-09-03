import json
import uuid


def add_change_request(file_path: str, line_number: int,
                       new_code: str, review_comment: str):
    change_id = str(uuid.uuid4())
    with open(f'.bots/response/change_requests/{change_id}.json', 'w') as f:
        json.dump({file_path: file_path, line_number: line_number,
                  new_code: new_code, review_comment: review_comment}, f)
