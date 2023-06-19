from pathlib import Path
import yaml

CONFIG_FILE = Path("config.yaml")
DEFAULT_VALUES = {
    "version": "0.2.7",
    "author": "ne0liberal",
    "root_dir": "D:/Content/ISOs",
    "completion_json": "D:/Content/index.json",
    "history_file": "D:/Content/history/history.json",
    "premium_directory": "premium",
    "output_attributes": False,
    "is_dry_run": True,
    "is_debug": True,
    "do_imports": True,
    "do_renames": True,
    "do_renames_lowercase": True,
    "do_converts": True,
    "do_clean_duplicate_extensions": False,
    "do_premium_imports": True,
    "do_loose_file_imports": True,
    "do_image_converts": False,
    "do_video_converts": False,
    "do_import_coomer": True,
    "do_import_fanhouse": True,
    "do_import_fansly": True,
    "do_import_gumroad": True,
    "do_import_onlyfans": True,
    "do_import_patreon": True,
    "do_import_ppv": True,
    "valid_filetypes": {
        "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
        "images": [
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".webp",
            ".jfif",
        ],
        "text": [".txt", ".doc", ".docx", ".pdf", ".rtf"],
        "misc": [
            ".zip",
            ".rar",
            ".7z",
            ".torrent",
            ".heic",
            ".log",
            ".db",
            ".htm",
            ".html",
            ".bat",
            ".py",
            ".db-journal",
            ".ini",
            ".psd",
            ".time",
        ],
        "videos": [
            ".mp4",
            ".mkv",
            ".mov",
            ".m4v",
            ".wmv",
            ".webm",
            ".gif",
            ".avi",
            ".ts",
            ".mpg",
            ".flv",
            ".mpeg",
        ],
    },
    "goal_video_extensions": [".mp4", ".webm", ".gif"],
    "goal_image_extensions": [".jpg", ".webp"],
    "convertable_video_extensions": [
        ".avi",
        ".m4v",
        ".mkv",
        ".mov",
        ".mpeg",
        ".ts",
        ".wmv",
        ".vid",
    ],
    "convertable_image_extensions": [".jfif", ".jpeg", ".png"],
    "protected_models": ["darshelle stevens", "jessica nigri", "meg turney"],
    "protected_dirs": ["corrupted", "favorites", "premium", "youtube"],
}


def main():
    try:
        generate_config(CONFIG_FILE)
        print(f"Successfully generated config file: {CONFIG_FILE}\n")
    except Exception as e:
        print(f"Failed to generate config file: {e}\n")

    input("Press enter to exit...")


def generate_config(config_file: Path):
    existing_config = {}

    config_file = config_file.resolve()

    if config_file.exists():
        if config_file.stat().st_size > 0:
            with open(config_file, "r") as f:
                existing_config = yaml.safe_load(f)

    config_data = {**DEFAULT_VALUES, **existing_config}

    with open(config_file, "w") as f:
        yaml.dump(config_data, f, sort_keys=False, indent=4)


if __name__ == "__main__":
    main()
