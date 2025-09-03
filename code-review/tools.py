import json


def add_change_request(file_path: str, line_number: int,
                       new_code: str, review_comment: str):
    // AI!: generate UUID
    with open(f'.bots/response/change_requests/{uuid}.json', 'w') as f:
        json.dump({file_path: file_path, line_number: line_number,
                  new_code: new_code, review_comment: review_comment}, f)
