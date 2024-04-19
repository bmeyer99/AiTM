from flask import request, jsonify
from .decorators import token_required, handle_exceptions
from bson import ObjectId
from datetime import datetime
from utils.tools import bson_to_json, compress_history
from db_setup import (
    tasks_collection,
    attachments_collection,
    profiles_collection,
    send_transaction,
)
import uuid
import boto3
from botocore.exceptions import NoCredentialsError


def register_attachment_routes(app):

    @handle_exceptions
    @app.route("/api/attachment/<attach_id>", methods=["GET", "POST", "DELETE"])
    @token_required
    def attachments(attach_id, cognito_id):
        incoming_attachment = request.json.get("attachments", {})
        if len(attach_id) < 3:
            owned_attachment = None
        else:
            owned_attachment = attachments_collection.find_one(
                {"_id": ObjectId(attach_id)}
            )
            if cognito_id != owned_attachment["owner_id"]:
                return {"message": "Unauthorized"}, 403
            if not owned_attachment:
                return {"message": "Attachment not found"}, 404

        if request.method == "GET":
            if attach_id == "0":
                owned_attachments = [
                    bson_to_json(owned_attachment)
                    for owned_attachment in attachments_collection.find(
                        {"owner_id": cognito_id}
                    )
                ]
                return {"owned_attachments": owned_attachments}

            if len(attach_id) > 3:
                owned_attachment = attachments_collection.find({"_id": attach_id})
                return bson_to_json(owned_attachment)

        if request.method == "POST":
            if attach_id != "0":
                return {"message": "Invalid request"}, 400
            if incoming_attachment is None:
                return {"message": "No attachment in body"}, 400
            if incoming_attachment["task_id"] is None:
                return {"message": "No task_id in body"}, 400

            def create_attachment(session):
                attachments_collection.update_one(
                    {"_id": ObjectId(attach_id)},
                    {"$set": incoming_attachment},
                    session=session,
                )

            def update_task(session):
                tasks_collection.update_one(
                    {"_id": ObjectId(incoming_attachment["task_id"])},
                    {"$push": {"attachments": incoming_attachment["_id"]}},
                    session=session,
                )

            def update_profile_history(session):
                result = create_attachment(session)
                profiles_collection.update_one(
                    {"_id": ObjectId(cognito_id)},
                    {
                        "$push": {
                            "history": {
                                "Attachment Created": {
                                    str(result.inserted_id): incoming_attachment
                                },
                                "timestamp": datetime.utcnow(),
                            }
                        }
                    },
                    session=session,
                )

            return send_transaction(
                [create_attachment, update_task, update_profile_history]
            )

        if request.method == "DELETE" and len(attach_id) > 3:
            if incoming_attachment is None:
                return {"message": "No task in body"}, 400
            if incoming_attachment["delete_from"] != owned_attachment["task_id"]:
                return ({"message": "Task_id does not match attachment"}), 400
            history_push = {
                "$push": {
                    "history": {
                        "Attachment Deleted": {
                            owned_attachment["_id"]: compress_history(owned_attachment),
                            "timestamp": datetime.utcnow(),
                        }
                    },
                },
            }

            def update_task_history(session):
                tasks_collection.update_one(
                    {"_id": ObjectId(incoming_attachment["delete_from"])},
                    {"$pull": {"attachments": attach_id}},
                    history_push,
                    session=session,
                )

            def update_profile_history(session):
                profiles_collection.update_one(
                    {"cognito_id": ObjectId(cognito_id)},
                    history_push,
                    session=session,
                )

            def update_attachment(session):
                attachments_collection.delete_one({"_id": ObjectId(attach_id)})

            return send_transaction(
                [update_task_history, update_profile_history, update_attachment]
            )

    # provide a presigned url to the user to be able to upload an attachment to s3
    @handle_exceptions
    @app.route("/api/attachment/get_signed_url/", methods=["GET"])
    @token_required
    def create_presigned_url(cognito_id):
        bucket_name = "task-manager-attachments"
        file_id = str(uuid.uuid4())
        s3key = f"{cognito_id}/{file_id}"
        try:
            s3_client = boto3.client("s3")
            response = s3_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket_name, "Key": s3key},
                ExpiresIn=300,
            )  # Default expiration time
            return jsonify({"url": response, "fileID": file_id})
        except NoCredentialsError:
            return jsonify({"message": "No AWS credentials found"}), 500
