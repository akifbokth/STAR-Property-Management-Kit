import os

def cleanup_temp_preview_folder(folder="temp_preview"):
    if not os.path.exists(folder):
        return
    for f in os.listdir(folder):
        try:
            os.remove(os.path.join(folder, f))
        except Exception as e:
            print(f"[Cleanup] Could not remove file: {f} — {e}")
