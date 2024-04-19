from flask import request
from .decorators import token_required, handle_exceptions
from bson import ObjectId
from datetime import datetime
import json
from utils.tools import (
    bson_to_json,
    compress_history,
)
from db_setup import (
    tasks_collection,
    attachments_collection,
    profiles_collection,
    boards_collection,
    send_transaction,
)


def register_profiles_routes(app):

    @app.route("/api/profile/", methods=["POST", "PUT", "DELETE", "GET"])
    @handle_exceptions
    @token_required
    def profile(cognito_id):
        incoming_profile = request.json.get("profile", {})
        if request.method == "POST":
            if incoming_profile is None:
                return {"message": "No profile in body"}, 400
            incoming_profile.update(
                {
                    "owner_id": cognito_id,
                    "creation_time": datetime.utcnow(),
                    "history": [{"Profile Created": str(datetime.utcnow())}],
                    "login_history": [datetime.utcnow()],
                }
            )
            result = profiles_collection.insert_one(incoming_profile)
            return {"created_id": str(result.inserted_id)}, 201

        if request.method in ["GET", "PUT", "DELETE"]:
            try:
                owned_profile = bson_to_json(
                    profiles_collection.find_one({"owner_id": cognito_id})
                )
            except Exception as e:
                return {"message": "No profile found", "error": str(e)}, 500
            profile_id = owned_profile["_id"]
            if cognito_id != owned_profile["owner_id"]:
                return {"message": "Unauthorized"}, 403

            if request.method == "GET":
                return owned_profile

            if request.method == "PUT":
                try:
                    profiles_collection.update_one(
                        {"_id": ObjectId(profile_id)},
                        {
                            "$set": request.json["profile"],
                            "$push": {
                                "history": {
                                    "Profile Updated": {
                                        "updated_details": request.json["profile"],
                                        "original_details": compress_history(
                                            owned_profile
                                        ),
                                        "timestamp": str(datetime.utcnow()),
                                    }
                                },
                            },
                        },
                    )
                    return "", 200
                except Exception as e:
                    return {"message": str(e)}, 500

            if request.method == "DELETE":

                def delete_attachments(session):
                    attachments_collection.delete_many(
                        {"owner_id": cognito_id}, session=session
                    )

                def delete_tasks(session):
                    tasks_collection.delete_many(
                        {"owner_id": cognito_id}, session=session
                    )

                def delete_boards(session):
                    boards_collection.delete_many(
                        {"owner_id": cognito_id}, session=session
                    )

                def delete_profile(session):
                    profiles_collection.delete_one(
                        {"_id": ObjectId(profile_id)}, session=session
                    )

                def tasks_remove_shared_with(session):
                    tasks_collection.update_many(
                        {"members": cognito_id},
                        {"$pull": {"members": cognito_id}},
                        session=session,
                    )

                return send_transaction(
                    [
                        delete_attachments,
                        delete_tasks,
                        delete_boards,
                        delete_profile,
                        tasks_remove_shared_with,
                    ]
                )

            else:
                return {"message": "Profile not found"}, 404
