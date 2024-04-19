from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pymongo.errors import PyMongoError


load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
aitm_db = client["task_manager"]

attachments_collection = aitm_db["attachments"]
tasks_collection = aitm_db["tasks"]
boards_collection = aitm_db["boards"]
profiles_collection = aitm_db["profiles"]


def execute_in_transaction(operations, session):
    try:
        for operation in operations:
            operation(session)
        session.commit_transaction()
        return 0
    except PyMongoError:
        session.abort_transaction()
        return ({"message": "An error occurred while trying to update the board"}), 500


def send_transaction(funcs_to_process):
    with client.start_session() as session:
        try:
            session.start_transaction()
            result = None
            for func in funcs_to_process:
                result = func(session)
            session.commit_transaction()
            return result
        except Exception as e:
            session.abort_transaction()
            return {"message": f"An error occurred: {str(e)}"}, 500
