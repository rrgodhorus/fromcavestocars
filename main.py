# main.py
# Entry point for the Flask application for buildpack deployment on Google Cloud

import os
import shutil

# Copy example data files to their target locations at startup
def copy_example_data():
    """
    Recursively copy everything under exampledatafiles/ into the project root,
    preserving directory structure.
    """
    # Determine source and destination roots
    src_root = os.path.join(os.path.dirname(__file__), 'exampledatafiles')
    dst_root = os.path.dirname(__file__)

    if os.path.exists(src_root):
        for root, dirs, files in os.walk(src_root):
            # Compute path relative to exampledatafiles
            rel_path = os.path.relpath(root, src_root)
            # Determine corresponding target directory in project root
            target_dir = os.path.join(dst_root, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            # Copy each file to the target directory
            for filename in files:
                src_file = os.path.join(root, filename)
                dst_file = os.path.join(target_dir, filename)
                shutil.copy2(src_file, dst_file)
                print(f"Copied {src_file} to {dst_file}")

# Perform the copy before importing the app
def pre_startup():
    try:
        copy_example_data()
    except Exception as e:
        print(f"Warning: failed to copy example data files: {e}")

pre_startup()

# Import the Flask app instance from your application module
from fromcavestocars import app

if __name__ == "__main__":
    # When running locally, enable debug mode and listen on all interfaces
    # Note: In Google Cloud, Gunicorn will be used instead of this block
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

