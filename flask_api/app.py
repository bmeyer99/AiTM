from routes.tasks import register_tasks_routes
from routes.boards import register_boards_routes
from routes.profiles import register_profiles_routes
from routes.attachments import register_attachment_routes

from flask import Flask

app = Flask(__name__)

# Register the routes with the Flask application instance
register_tasks_routes(app)
register_boards_routes(app)
register_profiles_routes(app)
register_attachment_routes(app)
print(app.url_map)

# RUNTIME
if __name__ == "__main__":
    app.run(debug=True)
