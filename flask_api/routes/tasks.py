from flask import Flask, request
from .decorators import token_required, handle_exceptions
from bson import ObjectId
from datetime import datetime
from db_setup import tasks_collection, profiles_collection, send_transaction
from utils.tools import (
    bson_to_json,
    compress_history,
    remove_task_references_in_attachments,
)
import json


def register_tasks_routes(app):
    @app.route("/api/task/<task_id>", methods=["GET", "POST", "PUT", "DELETE"])
    @handle_exceptions
    @token_required
    def tasks(task_id, cognito_id):
        incoming_task = request.json
        if len(task_id) < 3:
            owned_task = None
        else:
            owned_task = bson_to_json(
                tasks_collection.find_one({"_id": ObjectId(task_id)})
            )
            if (
                cognito_id != owned_task["owner"]
                and cognito_id not in owned_task["members"]
            ):
                return {"message": "Unauthorized"}, 403

        # If the request is GET and the task_id is 1, return all tasks
        if request.method == "GET":
            if task_id == "0":
                owned_tasks = [
                    bson_to_json(task)
                    for task in tasks_collection.find({"owner_id": cognito_id})
                ]
                shared_tasks = [
                    bson_to_json(task)
                    for task in tasks_collection.find({"members": cognito_id})
                ]
                return {"owned_tasks": owned_tasks, "shared_tasks": shared_tasks}

            if len(task_id) > 3:
                return bson_to_json(
                    tasks_collection.find_one({"_id": ObjectId(task_id)})
                )

        # If the request is POST, create a new task
        if request.method == "POST" and task_id == "0":
            if incoming_task is None:
                return {"message": "No task in body"}, 400
            incoming_task.update(
                {
                    "owner_id": cognito_id,
                    "created_at": datetime.utcnow(),
                    "history": {"Task Created": datetime.utcnow()},
                }
            )

            def create_task(session):
                result = tasks_collection.insert_one(incoming_task, session=session)
                return result

            def update_profile(session):
                result = create_task(session)
                result = str(result.inserted_id)
                profiles_collection.update_one(
                    {"_id": ObjectId(cognito_id)},
                    {
                        "$push": {
                            "history": {
                                "Task Created": {
                                    result: incoming_task,
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                        },
                    },
                    session=session,
                )

            result = send_transaction([create_task])
            return {"taskId": str(result.inserted_id)}, 201

        if request.method == "PUT":

            def update_task(session):
                tasks_collection.update_one(
                    {"_id": ObjectId(task_id)},
                    {
                        "$set": request.json["tasks"],
                    },
                    session=session,
                )

            def update_profile(session):
                result = update_task(session)
                profiles_collection.update_one(
                    {"owner_id": cognito_id},
                    {
                        "$push": {
                            "history": {
                                "Task Updated": {
                                    str(result.inserted_id): incoming_task,
                                    "previous_details": compress_history(owned_task),
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                        },
                    },
                    session=session,
                )

            return send_transaction([update_profile, update_task])

        if request.method == "DELETE":
            if owned_task:

                def update_task(session):
                    remove_task_references_in_attachments(task_id)
                    tasks_collection.delete_one(
                        {"_id": ObjectId(task_id)},
                        session=session,
                    )
                    return {"message": "Task deleted"}

                def update_profile(session):
                    profiles_collection.update_one(
                        {"_id": ObjectId(cognito_id)},
                        {
                            "$push": {
                                "history": {
                                    "Task Deleted": {
                                        task_id: compress_history(owned_task),
                                        "timestamp": datetime.utcnow(),
                                    }
                                },
                            },
                        },
                        session=session,
                    )

        return send_transaction([update_task, update_profile])

    return {"message": "Task not found"}, 404
