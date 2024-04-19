import gzip, json
from db_setup import tasks_collection, attachments_collection
from bson.json_util import dumps
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId


def compress_history(history):
    return gzip.compress(json.dumps(history).encode("utf-8"))


def decompress_history(history):
    return json.loads(gzip.decompress(history).decode("utf-8"))


def bson_to_json(bson):
    return json.loads(dumps(bson))


def remove_task_references_in_attachments(task_id):
    # Pull the task_id from the attachments
    result = attachments_collection.update_many(
        {"task_id": task_id}, {"$pull": {"task_id": task_id}}
    )


def remove_task_references_in_attachments_from_board(board_id):
    # Find all tasks associated with the board
    tasks = bson_to_json(tasks_collection.find({"board_id": board_id}))

    for task in tasks:
        # Remove task reference in attachments
        remove_task_references_in_attachments(task["_id"])

def is_valid_id(id):
    return ObjectId.is_valid(id)
