# main.py
# Entry point for the Flask application for buildpack deployment on Google Cloud

import os
import shutil

# Path to the marker file indicating example data has been copied
COPIED_MARKER = os.path.join(os.path.dirname(__file__), '.data_copied')

# Ensure fromcavestocars.main() logic always runs, regardless of entrypoint
from fromcavestocars import main as run_app_main

# Copy example data files to their target locations at startup
def copy_example_data():
    """
    Recursively copy everything under exampledatafiles/ into the project root,
    preserving directory structure. Skips if already copied.
    """
    # If marker exists, skip copying
    if os.path.exists(COPIED_MARKER):
        print("Example data already copied; skipping.")
        return

    src_root = os.path.join(os.path.dirname(__file__), 'exampledatafiles')
    dst_root = os.path.dirname(__file__)

    if os.path.exists(src_root):
        for root, dirs, files in os.walk(src_root):
            rel_path = os.path.relpath(root, src_root)
            target_dir = os.path.join(dst_root, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            print(f"Copying files from {root} to {target_dir}")
            for filename in files:
                src_file = os.path.join(root, filename)
                dst_file = os.path.join(target_dir, filename)
                shutil.copy2(src_file, dst_file)

        # Create marker file to indicate completion
        try:
            with open(COPIED_MARKER, 'w') as f:
                f.write('copied')
        except Exception as e:
            print(f"Warning: could not write copy marker: {e}")

# Pre-startup tasks: data copy and app-specific main logic

def pre_startup():
    # Copy files if not done
    try:
        copy_example_data()
    except Exception as e:
        print(f"Warning: failed to copy example data files: {e}")

    # Always run the application module's main() logic
    try:
        run_app_main(clouddeploy=True)
    except Exception as e:
        print(f"Error in fromcavestocars.main(): {e}")

# Execute pre-startup before loading the Flask app
pre_startup()

# Import the Flask app instance from your application module
from fromcavestocars import app

if __name__ == "__main__":
    # When running locally, enable debug mode and listen on all interfaces
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

