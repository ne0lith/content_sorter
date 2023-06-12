import os
import re
import json
import time
import ftfy
import emoji
import shutil
import traceback
from tqdm import tqdm
from PIL import Image
from datetime import datetime
from pathlib import Path
from functools import partial
from multiprocessing import Pool
from sanitize_filename import sanitize


# notes
# modify lines: 43, 70, 585, 720, and 721
# line 43: this will be the subdir you want premium content to be moved to. i.e. all fansly/onlyfans/coomer content will be moved to "premium" subdir for that model
# line 70: this will be the location of where you want rename history to be stored
# line 575: where it says "collections" change that to the name of the root folder: i.e. if your root folder is "X:/Content/ISOs" then change it to "ISOs" # this needs to be dynamic, but lazy atm
# line 720: this will be the root path of where your files are located
# line 721: this will be where you want to store the export dict, i.e. log of every file this script came across

# my sanitize filename function is kind of meh, but its decent enough for me, i recommend disabling it for your own uses.
# also do_remove_de will remove duplicate extensions, i.e. "file.jpg.jpg" will be renamed to "file.jpg"
# be careful here! sometimes screenshot files will be named after the video, but still be .jpg, so you can have files named "video_name_102.mp4.jpg", which will become "video.jpg"

# what this does
# when given your root directory, it will go through all of your models folders, and move the folders to their proper subdirs
# i.e. all fansly/onlyfans/coomer/ppv content will be moved to the model/premium_subdir
# so far, we're importing onlyfans filenames properly, but ppv/fansly/patreon are guesses
# im unaware of how those files are named, so were just moving files to the premium subdir if they contain the string "ppv", "fansly", or "patreon" in the filename stem
# this also converts ".png", and ".jfif" to jpg. and ".jpeg" to ".jpg" just my preference, but you can disable this if you want

# some explanation
# protected_models
# these are model folders where you want NOTHING to be messed with, i.e. "darshelle stevens" is a model folder, but i dont want anything touched there since it's all curated
# protected_dirs
# these are folders you want to be ignored, i.e. "premium", "fix", "manual_review", "corrupted", "favorites", "sorted albums"
# if content is in one of these folders, in any model folder, it will be ignored

# final notes
# it takes my machine about ~50 seconds to iterate over a million files
# this isn't counting time for when it is doing something, just time to iterate when there isn't anything else to do.

# to do: we need to make sure model's loose files are properly moved to the correct subdir, i.e. "images", "videos".
# ive been using older scripts of mine to do this, but i want this to do everything, so this will be added soon
# also, my history implementation is atrocious, and it's constantly reading and recreating the file, so that needs to be fixed
# i want to store all history in memory, and then write it to file at the end, but i havent gotten around to it yet


def get_config():
    config = {
        "DRY_RUN": True,
        "DO_RENAMES": True,
        "DO_REMOVE_DUPLICATE_EXTENSIONS": True,
        "DO_CONVERTS": True,
        "DO_COOMER_IMPORTS": True,
        "DO_ONLYFANS_IMPORTS": True,
        "DO_FANSLY_IMPORTS": True,
        "DO_PATREON_IMPORTS": True,
        "DO_PPV_IMPORTS": True,
        "DO_IMAGE_CONVERTS": True,
        "PREMIUM_DIR": "premium",
        "VALID_FILETYPES": {
            "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
            "images": [".jpg", ".jpeg", ".png", ".bpm", ".tiff", ".webp", ".jfif"],
            "text": [".txt", ".doc", ".docx", ".pdf", ".rtf", ".xls", ".xlsx"],
            "heic": [".heic"],
            "torrent": [".torrent"],
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
        "PROTECTED_MODELS": [
            "darshelle stevens",
            "darshelle stevens - fix",
            "jessica nigri",
            "jessica nigri - fix",
            "meg turney",
            "meg turney - fix",
        ],
        "PROTECTED_DIRS": [
            "premium",
            "fix",
            "manual_review",
            "corrupted",
            "favorites",
            "sorted albums",
        ],
        "HISTORY_FILE": "A:/Venus/history/history.json",
    }

    # Check if all required keys are present
    required_keys = [
        "DRY_RUN",
        "DO_RENAMES",
        "DO_REMOVE_DUPLICATE_EXTENSIONS",
        "DO_CONVERTS",
        "DO_COOMER_IMPORTS",
        "DO_ONLYFANS_IMPORTS",
        "DO_FANSLY_IMPORTS",
        "DO_PATREON_IMPORTS",
        "DO_PPV_IMPORTS",
        "DO_IMAGE_CONVERTS",
        "PREMIUM_DIR",
        "VALID_FILETYPES",
        "PROTECTED_MODELS",
        "PROTECTED_DIRS",
        "HISTORY_FILE",
    ]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing keys in config: {missing_keys}")

    # Check the type of each value
    expected_types = {
        "DRY_RUN": bool,
        "DO_RENAMES": bool,
        "DO_REMOVE_DUPLICATE_EXTENSIONS": bool,
        "DO_CONVERTS": bool,
        "DO_COOMER_IMPORTS": bool,
        "DO_ONLYFANS_IMPORTS": bool,
        "DO_FANSLY_IMPORTS": bool,
        "DO_PATREON_IMPORTS": bool,
        "DO_PPV_IMPORTS": bool,
        "DO_IMAGE_CONVERTS": bool,
        "PREMIUM_DIR": str,
        "VALID_FILETYPES": dict,
        "PROTECTED_MODELS": list,
        "PROTECTED_DIRS": list,
        "HISTORY_FILE": str,
    }
    incorrect_types = [
        key
        for key, value_type in expected_types.items()
        if key in config and not isinstance(config[key], value_type)
    ]
    if incorrect_types:
        raise TypeError(f"Incorrect value types in config: {incorrect_types}")

    history_file = Path(config["HISTORY_FILE"])
    if not history_file.exists():
        try:
            history_file.touch()
        except Exception as e:
            raise ValueError(f"Could not create history file: {e}")

    return config


class FileProcessor:
    def __init__(self, root_dir, num_processes):
        self.root_dir = Path(root_dir)
        self.num_processes = num_processes

        self.progress_bar = None
        self.file_count = 0
        self.update_interval = 1350  # Adjust the interval as needed

        try:
            self.config = get_config()
        except Exception as e:
            if isinstance(e, ValueError):
                print(f"Config error: {e}")
            elif isinstance(e, TypeError):
                print(f"Config error: {e}")
            else:
                print(f"Unknown error: {e}")
                print(traceback.format_exc())
            input("Press enter to exit...")
            exit(1)

        self.result_dict = dict()
        self.history_file = Path(self.config["HISTORY_FILE"])

        self.premium_dir = self.config["PREMIUM_DIR"]

        self.protected_models = self.config["PROTECTED_MODELS"]
        self.protected_dirs = self.config["PROTECTED_DIRS"]

        self.dry_run = self.config["DRY_RUN"]
        self.do_renames = self.config["DO_RENAMES"]
        self.do_remove_de = self.config["DO_REMOVE_DUPLICATE_EXTENSIONS"]
        self.do_coomer_imports = self.config["DO_COOMER_IMPORTS"]
        self.do_onlyfans_imports = self.config["DO_ONLYFANS_IMPORTS"]
        self.do_fansly_imports = self.config["DO_FANSLY_IMPORTS"]
        self.do_patreon_imports = self.config["DO_PATREON_IMPORTS"]
        self.do_ppv_imports = self.config["DO_PPV_IMPORTS"]
        self.do_image_converts = self.config["DO_IMAGE_CONVERTS"]

        self.valid_filetypes = self.config["VALID_FILETYPES"]
        self.image_extensions = self.valid_filetypes["images"]
        self.video_extensions = self.valid_filetypes["videos"]
        self.goal_video_extension = [".mp4", ".webm", ".gif"]
        self.goal_image_extension = [".jpg", ".webp"]

        self.videos_to_convert = list()
        self.images_to_convert = list()

        self.actions_history = list()

    def crawl_root(self):
        start_time = time.time()

        self.progress_bar = tqdm(desc="Crawling", unit=" files", leave=False)
        pool = Pool(processes=self.num_processes)
        with pool:
            partial_process_file = partial(self.process_file)
            self.process_directory(self.root_dir, partial_process_file)
        self.progress_bar.close()

        total_time = time.time() - start_time
        total_files = sum(len(v) for v in self.result_dict.values())

        total_actions = len(self.actions_history)

        if total_actions == 0:
            print(f"\nTotal files checked: {self.file_count}")
            print(f"Total time: {total_time:.2f} seconds")
            print("No actions necessary!\n")

        if total_actions > 0:
            print("-----------------------------------\n")
            print(f"Total time: {total_time:.2f} seconds")
            print(f"Total files: {total_files}\n")

        if self.videos_to_convert:
            print(f"Total remnant videos to convert: {len(self.videos_to_convert)}")
            print("\nVideos to convert:")
            for video in self.videos_to_convert:
                print(str(video))

        if self.images_to_convert:
            print(f"Total remnant images to convert: {len(self.images_to_convert)}")
            print("\nImages to convert:")
            for image in self.images_to_convert:
                print(str(image))

        input("\nPress any key to exit...")

    def process_file(self, file_path):
        key = str(file_path.relative_to(self.root_dir).parts[0])

        value = file_path
        value = value.relative_to(self.root_dir)
        value = value.parent.name + "/" + value.name

        if key in self.result_dict:
            self.result_dict[key].append(value)
        else:
            self.result_dict[key] = [value]

        if not self.check_protected(file_path):
            # we dont want to touch files in these protected models directories
            model_path = self.get_model(file_path)
            if model_path in self.protected_models:
                return

            # we also dont want to touch files in these general protected directories
            segments = file_path.parts
            if any(segment.lower() in self.protected_dirs for segment in segments):
                return

            # append images files that arent the goal extension to the list of images to convert
            if file_path.suffix.lower() in self.image_extensions:
                if file_path.suffix.lower() not in self.goal_image_extension:
                    self.images_to_convert.append(file_path)

            # append video files that arent the goal extension to the list of videos to convert
            if file_path.suffix.lower() in self.video_extensions:
                if file_path.suffix.lower() not in self.goal_video_extension:
                    self.videos_to_convert.append(file_path)

            if self.do_coomer_imports:
                if self.is_coomer_file(file_path):
                    model_premium_dir = self.get_model_premium_dir(file_path)
                    if not model_premium_dir.exists():
                        model_premium_dir.mkdir()

                    input_path = file_path
                    output_path = model_premium_dir / file_path.name

                    # no other file *should* share the same name
                    # so i think we can safely delete the smaller file
                    # something we cant do with onlyfans files
                    # because sometimes leakers will rename files
                    if output_path.exists():
                        input_size = input_path.stat().st_size
                        output_size = output_path.stat().st_size

                        if input_size > output_size:
                            smallest_file = output_path
                        elif input_size < output_size:
                            smallest_file = input_path
                        else:
                            smallest_file = output_path

                        if not self.dry_run:
                            print(f"Deleting {smallest_file}")
                            smallest_file.unlink()
                        else:
                            print(f"Would delete {smallest_file}")

                        if not input_path.exists():
                            return

                    try:
                        output_filename = self.get_unique_file_path(
                            model_premium_dir / file_path.name
                        )
                        self.rename_file(file_path, output_filename)
                        self.actions_history.append(output_filename)
                    except Exception as e:
                        print(f"Error: {e}")
                        self.actions_history.append(output_filename)

            if self.do_onlyfans_imports:
                if self.is_onlyfans_file(file_path):
                    model_premium_dir = self.get_model_premium_dir(file_path)
                    if not model_premium_dir.exists():
                        model_premium_dir.mkdir()

                    input_path = file_path
                    output_path = model_premium_dir / file_path.name

                    output_path = self.get_unique_file_path(output_path)

                    if not self.dry_run:
                        self.rename_file(input_path, output_path)
                        self.actions_history.append(output_path)
                    else:
                        print(f"\nWould move {input_path} to {output_path}")
                        self.actions_history.append(input_path)

            if self.do_fansly_imports:
                if self.is_fansly_file(file_path):
                    model_premium_dir = self.get_model_premium_dir(file_path)
                    if not model_premium_dir.exists():
                        model_premium_dir.mkdir()

                    input_path = file_path
                    output_path = model_premium_dir / file_path.name

                    output_path = self.get_unique_file_path(output_path)

                    if not self.dry_run:
                        self.rename_file(input_path, output_path)
                        self.actions_history.append(output_path)
                    else:
                        print(f"\nWould move {input_path} to {output_path}")
                        self.actions_history.append(input_path)

            if self.do_patreon_imports:
                if self.is_patreon_file(file_path):
                    model_premium_dir = self.get_model_premium_dir(file_path)
                    if not model_premium_dir.exists():
                        model_premium_dir.mkdir()

                    input_path = file_path
                    output_path = model_premium_dir / file_path.name

                    output_path = self.get_unique_file_path(output_path)

                    if not self.dry_run:
                        self.rename_file(input_path, output_path)
                        self.actions_history.append(output_path)
                    else:
                        print(f"\nWould move {input_path} to {output_path}")
                        self.actions_history.append(input_path)

            if self.do_ppv_imports:
                if self.is_ppv_file(file_path):
                    model_premium_dir = self.get_model_premium_dir(file_path)
                    if not model_premium_dir.exists():
                        model_premium_dir.mkdir()

                    input_path = file_path
                    output_path = model_premium_dir / file_path.name

                    output_path = self.get_unique_file_path(output_path)

                    if not self.dry_run:
                        self.rename_file(input_path, output_path)
                        self.actions_history.append(output_path)
                    else:
                        print(f"\nWould move {input_path} to {output_path}")
                        self.actions_history.append(input_path)

            if self.do_remove_de:
                if self.has_duplicate_extensions(file_path):
                    new_filename = self.remove_duped_extensions(file_path.name)
                    new_file_path = file_path.parent / new_filename

                    if new_file_path != file_path:
                        if not self.dry_run:
                            self.rename_file(file_path, new_file_path)
                            self.actions_history.append(new_file_path)
                        else:
                            print(f"\nWould rename {file_path} to {new_file_path}")
                            self.actions_history.append(file_path)

            if self.do_renames:
                filename_original = file_path
                filename_new = self.sanitize_filename(file_path)
                if filename_original != filename_new:
                    if not self.dry_run:
                        self.rename_file(filename_original, filename_new)
                        self.actions_history.append(filename_new)
                    else:
                        print(f"\nWould rename {filename_original} to {filename_new}")
                        self.actions_history.append(filename_original)

            if self.do_image_converts:
                if file_path in self.images_to_convert:
                    if not self.dry_run:
                        try:
                            self.convert_to_jpg(file_path)
                            self.images_to_convert.remove(file_path)
                            self.actions_history.append(file_path.with_suffix(".jpg"))
                        except Exception as e:
                            print(f"Error: {e}")
                            self.actions_history.append(file_path)
                    else:
                        print(f"Would convert {file_path}")
                        self.actions_history.append(file_path)

            self.file_count += 1

            if self.file_count % self.update_interval == 0:
                self.progress_bar.update(self.update_interval)

    def process_directory(self, dir_path, partial_func, exclude_dirs=None):
        for entry in os.scandir(dir_path):
            if entry.is_file():
                partial_func(Path(entry.path))
            elif entry.is_dir():
                self.process_directory(entry.path, partial_func, exclude_dirs)

    def validate_path(self, file_path: Path):
        if not file_path.exists():
            return False
        return True

    def check_protected(self, file_path: Path):
        def is_protected_dir(file_path: Path):
            protected_dirs = [""]
            return any(dir in file_path.parts for dir in protected_dirs)

        def is_protected_file(file_path: Path):
            protected_suffixes = [".jpg", ".jpeg", ".mp4"]
            ig_twitter_file_pattern = re.compile(
                r".*(?:_n\.(?:jpe?g|mp4)|-img1\.(?:jpe?g|mp4)|-vid1\.mp4|_video_dashinit\.mp4)$"
            )
            name_regex = ig_twitter_file_pattern
            if any(suffix in file_path.suffix for suffix in protected_suffixes):
                if name_regex.match(file_path.name):
                    return True
            return False

        return is_protected_dir(file_path) or is_protected_file(file_path)

    def has_duplicate_extensions(self, file_path: Path):
        file_name = file_path.name

        parts = file_name.split(".")
        original_file_name = ".".join(parts[:-1])

        all_possible_extensions = self.video_extensions
        for ext in all_possible_extensions:
            if ext in original_file_name:
                return True
        return False

    def remove_duped_extensions(self, file_path: Path):
        file_path = Path(file_path)
        file_name = file_path.name
        parts = file_name.split(".")
        actual_suffix = parts[-1]

        all_possible_extensions = self.video_extensions

        new_file_name = ".".join(parts[:-1])

        for ext in all_possible_extensions:
            if ext in new_file_name:
                new_file_name = new_file_name.replace(ext, "")

        new_file_name = f"{new_file_name}.{actual_suffix}"

        if file_name == new_file_name:
            return file_name

        return new_file_name

    def is_coomer_file(self, file_path: Path):
        pattern = r"^[a-fA-F0-9]{64}$"

        if re.match(pattern, file_path.stem):
            return True
        return False

    def is_onlyfans_file(self, file_path: Path):
        def is_image(file_path):
            pattern = r"\d+x\d+_[a-z0-9]{32}"
            return (
                re.search(pattern, file_path.stem)
                and file_path.suffix.lower() in self.image_extensions
            )

        def is_video(file_path):
            pattern = r"[a-z0-9]{21}_source"
            return (
                re.search(pattern, file_path.stem)
                and file_path.suffix.lower() in self.video_extensions
            )

        return (
            is_image(file_path)
            or is_video(file_path)
            or "onlyfans" in file_path.stem.lower()
        )

    def is_fansly_file(self, file_path: Path):
        if "fansly" in file_path.stem.lower():
            return True
        return False

    def is_ppv_file(self, file_path: Path):
        if "ppv" in file_path.stem.lower():
            return True
        return False

    def is_patreon_file(self, file_path: Path):
        if "patreon" in file_path.stem.lower():
            return True
        return False

    def get_unique_file_path(self, file_path: Path) -> Path:
        file_name = file_path.stem
        file_ext = file_path.suffix

        unique_file_path = file_path

        if not file_path.exists():
            return unique_file_path

        attempts = 0
        while unique_file_path.exists():
            attempts += 1
            unique_file_path = file_path.with_name(
                f"{file_name}_duplicate_{attempts}{file_ext}"
            )

        return unique_file_path

    def convert_to_jpg(self, file_path: Path):
        file_path = Path(file_path)

        if "jpeg" in file_path.suffix.lower():
            output_path = file_path.with_suffix(".jpg")
            output_path = self.get_unique_file_path(output_path)
            file_path.rename(output_path)
            print(f"\nOriginal: {file_path}")
            print(f"New: {output_path}")
            return

        if file_path.suffix.lower() in [".png", ".jfif"]:
            try:
                image = Image.open(file_path)

                # Convert RGBA to RGB if image mode is RGBA
                if image.mode == "RGBA":
                    image = image.convert("RGB")

                output_path = file_path.with_suffix(".jpg")
                output_path = self.get_unique_file_path(output_path)
                image.save(output_path, "JPEG", quality=100)

                if output_path.is_file() and output_path.stat().st_size > 0:
                    print(f"\nOriginal: {file_path}")
                    print(f"New: {output_path}")
                    file_path.unlink()
                else:
                    print(
                        "Error occurred during conversion. Original file not deleted."
                    )
                    if output_path.is_file():
                        output_path.unlink()
            except Exception as e:
                print("Error occurred during conversion. Original file not deleted.")
                print(f"Error message: {str(e)}")
                if output_path.is_file():
                    output_path.unlink()

        else:
            print("File is not a PNG or JFIF.")
            self.images_to_convert.append(file_path)

    def get_model(self, file_path: Path) -> str:
        file_model = file_path.parts[file_path.parts.index("collections") + 1]

        return file_model

    def get_model_premium_dir(self, file_path: Path) -> Path:
        file_model = self.get_model(file_path)
        model_premium_dir = self.root_dir / file_model / self.premium_dir
        return model_premium_dir

    def sanitize_filename(self, file_path: Path):
        def remove_halfwidth_fullwidth_characters(filename):
            return ftfy.fix_text(filename, normalization="NFKC")

        def remove_emojis(filename):
            return emoji.replace_emoji(filename, "")

        def remove_invalid_characters(filename):
            return ftfy.fix_text(filename)

        def remove_capital_letters(filename):
            if any(c.isupper() for c in filename):
                return filename.lower()
            else:
                return filename

        def remove_double_spaces(filename):
            return re.sub(r"\s+", " ", filename)

        def remove_trailing_characters(filename):
            while len(filename) > 0:
                if filename[-1] in [".", "_", "-"]:
                    filename = filename[:-1]
                else:
                    break
            return filename

        def jpeg_to_jpg(filename):
            if filename.suffix == ".jpeg":
                return filename.with_suffix(".jpg")
            return filename

        filename = file_path.stem
        filename = remove_halfwidth_fullwidth_characters(filename)
        filename = remove_emojis(filename)
        filename = remove_invalid_characters(filename)
        filename = remove_capital_letters(filename)
        filename = remove_double_spaces(filename)
        filename = remove_trailing_characters(filename)
        filename = sanitize(filename)
        filename = file_path.parent / (filename + file_path.suffix)
        sanitized_filename = filename
        sanitized_filename = jpeg_to_jpg(filename)

        return sanitized_filename

    def _write_history(self, input_path: Path, output_path: Path):
        if not self.history_file.exists():
            self.history_file.touch(exist_ok=True)

        history_entry = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "timestamp": datetime.now().isoformat(),
        }

        history_dict = self._load_history()

        history_dict[history_entry["timestamp"]] = (
            str(input_path),
            str(output_path),
        )

        with open(self.history_file, "w") as history_file:
            json.dump(history_dict, history_file)

        self._backup_history()

    def _load_history(self):
        if not self.history_file.exists() or self.history_file.stat().st_size == 0:
            return {}

        self._backup_history()

        with open(self.history_file, "r") as history_file:
            return json.load(history_file)

    def _backup_history(self):
        backup_file = self.history_file.with_suffix(self.history_file.suffix + ".bak")

        if backup_file.exists():
            backup_file.unlink()

        shutil.copy2(self.history_file, backup_file)

    def rename_file(self, input_path: Path, output_path: Path):
        if not self.validate_path(input_path):
            print(f"Invalid path: {input_path}")
            return

        try:
            if not self.dry_run:
                input_path.rename(output_path)
                self._write_history(input_path, output_path)
            else:
                print("\nStatus: Dry run")

            print(f"\nOriginal: {input_path}")
            print(f"New:      {output_path}")

        except FileExistsError:
            input_size = input_path.stat().st_size
            output_size = output_path.stat().st_size

            if input_size == output_size:
                input_path.unlink()
                return
            else:
                potential_output_path = self.get_unique_file_path(output_path)
                if (
                    potential_output_path != input_path
                    and potential_output_path != output_path
                ):
                    self.rename_file(input_path, potential_output_path)

        except Exception as e:
            traceback.print_exc()
            print(f"Could not rename {input_path}: {e}")
            input("Press enter to continue...")

    def export_dict(self, output_path: Path, result_dict=None):
        with open(output_path, "w") as f:
            json.dump(
                self.result_dict,
                f,
                indent=4,
                default=lambda x: x.decode() if isinstance(x, bytes) else x,
            )


def main():
    venus_path = Path("A:/Venus/collections")
    export_json = Path("A:/Venus/collections.json")

    os.system("cls")
    processor = FileProcessor(venus_path, 10)
    processor.crawl_root()
    processor.export_dict(str(export_json), processor.result_dict)


if __name__ == "__main__":
    main()
