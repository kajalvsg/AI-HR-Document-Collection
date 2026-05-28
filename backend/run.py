import os

# Ensure backend/.env is loaded before the Flask app factory runs.
from app.config import load_environment

load_environment()

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=app.debug)
