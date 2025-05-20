import os
from config import TEMP_PREVIEW_DIR

def cleanup_temp_preview_folder():
    # Clear the temporary preview folder
    # This is used to remove any temporary files that may have been created
    folder = TEMP_PREVIEW_DIR
    if not os.path.exists(folder):
        return
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"[Cleanup] Could not remove {filename}: {e}")
