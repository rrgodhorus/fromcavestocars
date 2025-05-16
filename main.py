# main.py
# Entry point for the Flask application for buildpack deployment on Google Cloud

# Import the Flask app instance from your application module
from fromcavestocars import app

# If your app is created via a factory function, you might do:
# from fromcavestocars import create_app
# app = create_app()

if __name__ == "__main__":
    # When running locally, enable debug mode and listen on all interfaces
    # Note: In Google Cloud, Gunicorn will be used instead of this block
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

