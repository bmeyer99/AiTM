from flask import request
from .decorators import token_required, handle_exceptions
from bson import ObjectId
from datetime import datetime
from utils.tools import (
    bson_to_json,
    compress_history,
    remove_task_references_in_attachments_from_board,
    is_valid_id,
)
from db_setup import (
    boards_collection,
    profiles_collection,
    tasks_collection,
    send_transaction,
)
import json


def register_boards_routes(app):

    @app.route("/api/board/<board_id>", methods=["POST", "GET", "PUT", "DELETE"])
    @handle_exceptions
    @token_required
    def boards(board_id, cognito_id):
        incoming_board = request.json
        if request.method == "POST":
            if board_id != "0":
                return {"message": "Invalid request"}, 400
            if board_id is None:
                return {"message": "No board in body"}, 400
            if incoming_board is None:
                return {"message": "No board in body"}, 400

            incoming_board.update(
                {
                    "owner_id": cognito_id,
                    "created_at": datetime.utcnow(),
                }
            )

            def create_board(session):
                result = boards_collection.insert_one(incoming_board, session=session)
                return result.inserted_id

            def update_profile(session):
                inserted_id = create_board(session)
                profiles_collection.update_one(
                    {"owner_id": cognito_id},
                    {
                        "$push": {
                            "history": {
                                "Board Created": {
                                    inserted_id: incoming_board,
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                            "boards": inserted_id,
                        },
                    },
                    session=session,
                )
                print(f"Inserted ID: {inserted_id}")
                return inserted_id

            result = send_transaction([update_profile])
            return {"created_id": result}, 201

        if len(board_id) < 3:
            owned_board = {}
        else:
            owned_board = bson_to_json(
                boards_collection.find_one({"_id": ObjectId(board_id)})
            )
            if cognito_id != owned_board["owner_id"]:
                return {"message": "Unauthorized"}, 403
            if not owned_board:
                return {"message": "Board not found"}, 404

        # Get all boards
        if request.method == "GET" and board_id == "0":
            owned_boards = [
                bson_to_json(board)
                for board in boards_collection.find({"owner_id": cognito_id})
            ]
            shared_boards = [
                bson_to_json(board)
                for board in boards_collection.find({"members": cognito_id})
            ]
            return {"owned_boards": owned_boards, "shared_boards": shared_boards}

        # Get a list of all boards' names
        if request.method == "GET" and board_id == "1":
            owned_boards = [
                board["name"]
                for board in boards_collection.find(
                    {"owner_id": cognito_id}, {"name": 1}
                )
                if "name" in board
            ]
            shared_boards = [
                board["name"]
                for board in boards_collection.find(
                    {"members": cognito_id}, {"name": 1}
                )
                if "name" in board
            ]
            return {"owned_boards": owned_boards, "shared_boards": shared_boards}

        if request.method == "GET" and len(board_id) > 2:
            if owned_board:
                return owned_board
            return {"message": "Board not found"}, 404

        if request.method == "DELETE":
            if owned_board:

                def delete_board(session):
                    remove_task_references_in_attachments_from_board(board_id)
                    boards_collection.delete_one(
                        {"_id": ObjectId(board_id)}, session=session
                    )

                def profile_delete(session):
                    profiles_collection.update_one(
                        {"owner_id": cognito_id},
                        {
                            "$pull": {
                                "boards": {"_id": ObjectId(board_id)},
                            },
                        },
                        {
                            "$push": {
                                "history": {
                                    "Board Deleted": {
                                        board_id: compress_history(owned_board),
                                        "timestamp": datetime.utcnow(),
                                    }
                                },
                            },
                        },
                        session=session,
                    )

            return send_transaction([delete_board, profile_delete])

        if request.method == "PUT":
            if owned_board is None:
                return {"message": "Board not found"}, 404

            def update_board(session):
                boards_collection.update_one(
                    {"_id": ObjectId(board_id)},
                    {
                        "$set": incoming_board,
                        "$push": {
                            "history": {
                                "Board Updated": {
                                    board_id: incoming_board,
                                    "original_details": compress_history(owned_board),
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                        },
                    },
                    session=session,
                )

            def update_profile(session):
                result = update_board(session)
                profiles_collection.update_one(
                    {"owner_id": cognito_id},
                    {
                        "$push": {
                            "history": {
                                "Board Updated": {
                                    board_id: incoming_board,
                                    "previous_details": compress_history(owned_board),
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                        },
                    },
                    session=session,
                )

        return send_transaction([update_board, update_profile])

    @app.route("/api/stages/<board_id>", methods=["POST", "GET", "PUT", "DELETE"])
    @handle_exceptions
    @token_required
    def stages(board_id, cognito_id):
        incoming_stage = request.json.get("stages", "")

        if not is_valid_id(board_id):
            return {"message": "Invalid board ID"}, 400
        if request.method == "POST":
            if board_id is None:
                return {"message": "No board in body"}, 400
            if incoming_stage is "":
                return {"message": "No stage in body"}, 400

            def create_stage(session):
                boards_collection.update_one(
                    {"_id": ObjectId(board_id)},
                    {
                        "$push": {
                            "stages": incoming_stage,
                        },
                    },
                    session=session,
                )
                return incoming_stage

            def update_profile(session):
                profiles_collection.update_one(
                    {"owner_id": cognito_id},
                    {
                        "$push": {
                            "history": {
                                "Stages Updated": {
                                    board_id: incoming_stage,
                                    "timestamp": datetime.utcnow(),
                                }
                            },
                        },
                    },
                    session=session,
                )

            return send_transaction([update_profile, create_stage]), 201

        if request.method == "DELETE":

            def remove_stage(board_id):
                tasks_with_stage = tasks_collection.find(
                    {"board_id": board_id, "stage": incoming_stage}
                )
                if tasks_with_stage.count() > 0:
                    return {"message": "stage not empty"}
                else:
                    boards_collection.update_one(
                        {"_id": ObjectId(board_id)},
                        {"$pull": {"stages": incoming_stage}},
                    )
                    profiles_collection.update_one(
                        {"owner_id": cognito_id},
                        {
                            "$push": {
                                "history": {
                                    "Stages Deleted": {
                                        "board": board_id,
                                        "timestamp": datetime.utcnow(),
                                    }
                                },
                            },
                        },
                    )
                    return {"message": "success"}

            return send_transaction([remove_stage])
        return {"message": "Invalid request"}, 400
