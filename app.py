import os
import re
import sys
import builtins
import json
import time
import ftfy
import emoji
import shutil
import traceback
import uuid
import datetime
from tqdm import tqdm
from PIL import Image
from pathlib import Path
from functools import partial
from multiprocessing import Pool
from sanitize_filename import sanitize


def get_config():
    config = {
        "VERSION": "0.1.1",
        "AUTHOR": "ne0liberal",
        "ROOT_DIR": Path("A:/Venus/collections"),
        "COMPLETION_JSON": Path("A:/Venus/collections.json"),
        "HISTORY_FILE": Path("A:/Venus/history/history.json"),
        "PREMIUM_DIR": "premium",
        "IS_DRY_RUN": False,
        "IS_DEBUG": False,
        "DO_IMPORTS": True,
        "DO_RENAMES": True,
        "DO_CONVERTS": True,
        "DO_SANITIZE_FILENAMES": True,
        "DO_REMOVE_DUPLICATE_EXTENSIONS": True,
        "DO_PREMIUM_IMPORTS": True,
        "DO_LOOSE_FILE_IMPORTS": True,
        "DO_IMAGE_CONVERTS": True,
        "DO_IMPORT_COOMER": True,
        "DO_IMPORT_FANHOUSE": True,
        "DO_IMPORT_FANSLY": True,
        "DO_IMPORT_GUMROAD": True,
        "DO_IMPORT_ONLYFANS": True,
        "DO_IMPORT_PATREON": True,
        "DO_IMPORT_PPV": True,
        "VALID_FILETYPES": {
            "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
            "images": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".jfif"],
            "text": [".txt", ".doc", ".docx", ".pdf", ".rtf", ".xls", ".xlsx"],
            "misc": [".zip", ".rar", ".7z", ".torrent", ".heic"],
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
        "GOAL_VIDEO_EXTENSION": [".mp4", ".webm", ".gif"],
        "GOAL_IMAGE_EXTENSION": [".jpg", ".webp"],
        "PROTECTED_MODELS": [
            "darshelle stevens",
            "darshelle stevens - fix",
            "darshelle - jessica - meg crossovers",
            "jessica nigri",
            "jessica nigri - fix",
            "meg turney",
            "meg turney - fix",
            "virtual reality (vr)",
        ],
        "PROTECTED_DIRS": [
            "corrupted",
            "deepfakes",
            "favorites",
            "fix",
            "manual_review",
            "premium",
            "sorted albums",
            "youtube",
        ],
    }

    return config


class CustomEnvironment:
    def __init__(self):
        self.original_print = builtins.print
        self.original_input = builtins.input
        self.original_write = tqdm.write

        builtins.print = self.custom_print
        builtins.input = self.custom_input
        tqdm.write = self.custom_write

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()

    def custom_print(self, *args, **kwargs):
        modified_args = ("    " + str(arg) for arg in args)
        self.original_print(*modified_args, **kwargs)

    def custom_input(self, prompt=""):
        modified_prompt = "    " + prompt
        return self.original_input(modified_prompt)

    def custom_write(self, s, *args, **kwargs):
        modified_s = "    " + s
        self.original_write(modified_s, *args, **kwargs)

    def restore(self):
        builtins.print = self.original_print
        builtins.input = self.original_input
        tqdm.write = self.original_write


class History:
    def __init__(self, history_file):
        self.history_file = history_file
        self.history = self.load_history()

    def append_to_history(self, input_path, output_path):
        timestamp = datetime.datetime.now().timestamp()
        identifier = uuid.uuid4()

        entry = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "timestamp": str(timestamp),
        }

        self.history[str(identifier)] = entry

    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file, "r") as f:
                file_content = f.read()
                if file_content:
                    return json.loads(file_content)
        return dict()

    def save_history(self):
        self.backup_history()
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=4)

    def backup_history(self):
        if self.history_file.exists():
            shutil.copy(self.history_file, self.history_file.with_suffix(".bak"))


class FileProcessor:
    def __init__(self, num_processes):
        self.num_processes = num_processes

        self.config = get_config()
        for key in self.config.keys():
            setattr(self, key.lower(), self.config[key])
        self.history_instance = History(self.history_file)

        self.progress_bar = None
        self.file_count = 0
        self.update_interval = 850

        self.result_dict = dict()
        self.videos_to_convert = list()
        self.images_to_convert = list()
        self.actions_history = list()

        print("\n" + self.display_ascii_art() + "\n")
        print(f"Version: {self.version}")
        print(f" Author: {self.author}\n\n")

    def crawl_root(self):
        start_time = time.time()

        sys.stdout.write("\033[?25l")
        self.progress_bar = tqdm(
            desc=f'    Crawling "{self.root_dir}"',
            unit=" files",
            leave=False,
            bar_format="{l_bar} {n_fmt}{unit} ({rate_fmt}) [{elapsed}]",
        )

        pool = Pool(processes=self.num_processes)
        with pool:
            partial_process_file = partial(self.process_file)
            self.process_directory(self.root_dir, partial_process_file)
        self.progress_bar.close()
        sys.stdout.write("\033[?25h")

        self.history_instance.save_history()
        self.export_dict(str(self.completion_json), self.result_dict)

        total_time = time.time() - start_time

        print("-----------------------------------\n\n")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Total files: {self.file_count}\n\n")

        # patch until im better at tracking actions
        self.videos_to_convert, self.images_to_convert = [
            list(filter(lambda item: item.exists(), lst))
            for lst in (self.videos_to_convert, self.images_to_convert)
        ]

        if self.videos_to_convert:
            amnt = f"Videos to convert: ({len(self.videos_to_convert)})"
            print(amnt)
            print("-" * len(amnt))
            for video in self.videos_to_convert:
                print(str(video))

        if self.images_to_convert:
            if self.videos_to_convert:
                print()
            amnt = f"Images to convert: ({len(self.images_to_convert)})"
            print(amnt)
            print("-" * len(amnt))
            for image in self.images_to_convert:
                print(str(image))

        print()
        input("Press any key to exit...")

    def process_file(self, file_path):
        relative_path = file_path.relative_to(self.root_dir)
        key, value = (
            str(relative_path.parts[0]),
            f"{relative_path.parent.name}/{relative_path.name}",
        )

        if key in self.result_dict:
            self.result_dict[key].append(value)
        else:
            self.result_dict[key] = [value]

        self.file_count += 1

        if self.file_count % self.update_interval == 0:
            self.progress_bar.update(self.update_interval)

        if not self.check_protected(file_path):
            if (
                file_path.suffix.lower() in self.valid_filetypes["images"]
                and file_path.suffix.lower() not in self.goal_image_extension
            ):
                self.images_to_convert.append(file_path)

            if (
                file_path.suffix.lower() in self.valid_filetypes["videos"]
                and file_path.suffix.lower() not in self.goal_video_extension
            ):
                self.videos_to_convert.append(file_path)

            if self.do_converts:
                if self.do_image_converts:
                    if file_path in self.images_to_convert:
                        if not self.is_dry_run:
                            try:
                                self.convert_to_jpg(file_path)
                                if file_path in self.images_to_convert:
                                    self.images_to_convert.remove(file_path)
                                self.actions_history.append(
                                    file_path.with_suffix(".jpg")
                                )
                            except Exception as e:
                                tqdm.write(f"Error: {e}")
                                self.actions_history.append(file_path)
                        else:
                            tqdm.write(f"Would convert {file_path}")
                            self.actions_history.append(file_path)

            if self.do_imports:
                if self.do_premium_imports:
                    if self.is_premium_file(file_path):
                        model_premium_dir = self.get_model_premium_dir(file_path)
                        if not model_premium_dir.exists():
                            model_premium_dir.mkdir()

                        input_path = file_path
                        output_path = model_premium_dir / file_path.name
                        output_path = self.get_unique_file_path(output_path)

                        if not self.is_dry_run:
                            self.rename_file(input_path, output_path)
                            self.actions_history.append(output_path)
                        else:
                            tqdm.write(f"Would move {input_path} to {output_path}")

            if self.do_renames:
                if self.do_remove_duplicate_extensions:
                    if file_path.exists():
                        if self.has_duplicate_extensions(file_path):
                            new_filename = self.remove_duped_extensions(file_path.name)
                            new_file_path = file_path.parent / new_filename

                            if new_file_path != file_path:
                                if not self.is_dry_run:
                                    self.rename_file(file_path, new_file_path)
                                    self.actions_history.append(new_file_path)
                                else:
                                    tqdm.write(
                                        f"Would rename {file_path} to {new_file_path}"
                                    )
                                    self.actions_history.append(file_path)

                if self.do_sanitize_filenames:
                    if file_path.exists():
                        filename_original = file_path
                        filename_new = self.sanitize_filename(file_path)
                        if filename_original != filename_new:
                            if not self.is_dry_run:
                                self.rename_file(filename_original, filename_new)
                                self.actions_history.append(filename_new)
                            else:
                                tqdm.write(
                                    f"\nWould rename {filename_original} to {filename_new}"
                                )
                                self.actions_history.append(filename_original)

            if self.do_imports:
                if self.do_loose_file_imports:
                    if file_path.exists():
                        model_dir = self.get_model_name(file_path)
                        model_dir = self.root_dir / model_dir

                        if model_dir == file_path.parent and any(
                            file_path.suffix in filetypes
                            for filetypes in self.valid_filetypes.values()
                        ):
                            file_extension = file_path.suffix
                            subfolder = None

                            for key, filetypes in self.valid_filetypes.items():
                                if file_extension in filetypes:
                                    subfolder = key
                                    break

                            if subfolder is None:
                                subfolder = "misc"

                            subdir_path = model_dir / subfolder

                            if not subdir_path.exists():
                                if not self.is_dry_run:
                                    subdir_path.mkdir()
                                    self.actions_history.append(subdir_path)
                                else:
                                    tqdm.write(f"Would create {subdir_path}")

                            input_path = file_path
                            output_path = subdir_path / file_path.name

                            if not self.is_dry_run:
                                output_path = self.get_unique_file_path(output_path)
                                self.rename_file(input_path, output_path)
                                self.actions_history.append(output_path)
                            else:
                                tqdm.write(
                                    f"\nWould move {input_path} to {output_path}"
                                )

    def process_directory(self, dir_path, partial_func, exclude_dirs=None):
        if exclude_dirs is None:
            exclude_dirs = self.protected_dirs
            exclude_dirs += [self.root_dir / dir for dir in self.protected_models]

        # i believe this is a huge inefficiency
        # but don't know enough to figure out a better way
        for entry in os.scandir(dir_path):
            if entry.is_dir():
                skip_directory = False
                for exclude_dir in exclude_dirs:
                    if exclude_dir in Path(entry.path).parts or exclude_dir == Path(
                        entry.path
                    ):
                        skip_directory = True
                        break

                if skip_directory:
                    if self.is_debug:
                        tqdm.write(f"Skipping {entry.path}")
                    continue

                self.process_directory(entry.path, partial_func, exclude_dirs)
            elif entry.is_file():
                partial_func(Path(entry.path))

    def validate_path(self, path: Path, expect=None):
        if expect not in ["file", "dir"]:
            tqdm.write(f"Invalid expect value: {expect}. Must be 'file' or 'dir'")
            return False

        if not path.exists():
            return False

        if expect == "file":
            return path.is_file()
        elif expect == "dir":
            return path.is_dir()

        return False

    def check_protected(self, file_path: Path):
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

        return is_protected_file(file_path)

    def has_duplicate_extensions(self, file_path: Path):
        file_name = file_path.name

        parts = file_name.split(".")
        original_file_name = ".".join(parts[:-1])

        all_possible_extensions = (
            self.valid_filetypes["videos"] + self.valid_filetypes["images"]
        )
        for ext in all_possible_extensions:
            if ext in original_file_name:
                return True
        return False

    def remove_duped_extensions(self, file_path: Path):
        file_path = Path(file_path)
        file_name = file_path.name
        parts = file_name.split(".")
        actual_suffix = parts[-1]

        all_possible_extensions = (
            self.valid_filetypes["videos"] + self.valid_filetypes["images"]
        )

        new_file_name = ".".join(parts[:-1])

        for ext in all_possible_extensions:
            if ext in new_file_name:
                new_file_name = new_file_name.replace(ext, "")

        new_file_name = f"{new_file_name}.{actual_suffix}"

        if file_name == new_file_name:
            return file_name

        return new_file_name

    def is_premium_file(self, file_path: Path):
        def is_coomer_file(file_path):
            pattern = r"^[a-fA-F0-9]{64}$"
            return bool(re.match(pattern, file_path.stem))

        def is_fanhouse_file(file_path):
            return "fanhouse" in file_path.stem.lower()

        def is_fansly_file(file_path):
            return "fansly" in file_path.stem.lower()

        def is_gumroad_file(file_path):
            return "gumroad" in file_path.stem.lower()

        def is_onlyfans_file(file_path):
            def is_image(file_path):
                pattern = r"\d+x\d+_[a-z0-9]{32}"
                return (
                    re.search(pattern, file_path.stem)
                    and file_path.suffix.lower() in self.valid_filetypes["images"]
                )

            def is_video(file_path):
                pattern = r"[a-z0-9]{21}(_source|_720p|_1080p)"
                return (
                    re.search(pattern, file_path.stem)
                    and file_path.suffix.lower() in self.valid_filetypes["videos"]
                )

            return (
                is_image(file_path)
                or is_video(file_path)
                or "onlyfans" in file_path.stem.lower()
            )

        def is_patreon_file(file_path):
            return "patreon" in file_path.stem.lower()

        def is_ppv_file(file_path):
            pattern = r"pay[\s_-]*per[\s_-]*view"
            optional_patterns = ["ppv"]

            if any(pattern in file_path.stem.lower() for pattern in optional_patterns):
                return True

            return bool(re.search(pattern, file_path.stem.lower()))

        return (
            (self.do_import_coomer and is_coomer_file(file_path))
            or (self.do_import_fanhouse and is_fanhouse_file(file_path))
            or (self.do_import_fansly and is_fansly_file(file_path))
            or (self.do_import_gumroad and is_gumroad_file(file_path))
            or (self.do_import_onlyfans and is_onlyfans_file(file_path))
            or (self.do_import_patreon and is_patreon_file(file_path))
            or (self.do_import_ppv and is_ppv_file(file_path))
        )

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

            tqdm.write(f"Original: {file_path}")
            tqdm.write(f"     New: {output_path}\n")

            if file_path in self.images_to_convert:
                self.images_to_convert.remove(file_path)

            return

        if file_path.suffix.lower() in [".png", ".jfif"]:
            try:
                image = Image.open(file_path)

                if image.mode == "RGBA":
                    image = image.convert("RGB")

                output_path = file_path.with_suffix(".jpg")
                output_path = self.get_unique_file_path(output_path)
                image.save(output_path, "JPEG", quality=100)

                if file_path in self.images_to_convert:
                    self.images_to_convert.remove(file_path)

                if output_path.is_file() and output_path.stat().st_size > 0:
                    tqdm.write(f"Original: {file_path}")
                    tqdm.write(f"     New: {output_path}\n")
                    file_path.unlink()

                    if file_path in self.images_to_convert:
                        self.images_to_convert.remove(file_path)
                else:
                    tqdm.write(
                        "Error occurred during conversion. Original file not deleted.\n"
                    )
                    if output_path.is_file():
                        output_path.unlink()
            except Exception as e:
                tqdm.write(
                    "Error occurred during conversion. Original file not deleted.\n"
                )
                tqdm.write(f"Error message: {str(e)}\n")
                if output_path.is_file():
                    output_path.unlink()

        else:
            tqdm.write("File is not a PNG or JFIF.\n")
            self.images_to_convert.append(file_path)

    def get_model_name(self, file_path: Path) -> str:
        file_model = file_path.parts[file_path.parts.index("collections") + 1]

        return file_model

    def get_model_premium_dir(self, file_path: Path) -> Path:
        file_model = self.get_model_name(file_path)
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

    def rename_file(self, input_path: Path, output_path: Path):
        output_path = output_path.parent / output_path.name.lower()

        if not self.validate_path(input_path, expect="file"):
            tqdm.write(f"Invalid file path: {input_path}\n")
            return

        try:
            if not self.is_dry_run:
                input_path.rename(output_path)
                self.history_instance.append_to_history(input_path, output_path)
            else:
                tqdm.write("Status: Dry run")

            tqdm.write(f"Original: {input_path}")
            tqdm.write(f"     New: {output_path}\n")

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
            tqdm.write(f"Could not rename {input_path}: {e}\n")
            input("Press enter to continue...")

    def export_dict(self, output_path: Path, result_dict=None):
        with open(output_path, "w") as f:
            json.dump(
                self.result_dict,
                f,
                indent=4,
                default=lambda x: x.decode() if isinstance(x, bytes) else x,
            )

    def display_ascii_art(self):
        ascii_art = """
    :::     ::: :::::::::: ::::    ::: :::    :::  ::::::::  
    :+:     :+: :+:        :+:+:   :+: :+:    :+: :+:    :+: 
    +:+     +:+ +:+        :+:+:+  +:+ +:+    +:+ +:+        
    +#+     +:+ +#++:++#   +#+ +:+ +#+ +#+    +:+ +#++:++#++ 
    +#+   +#+  +#+        +#+  +#+#+# +#+    +#+        +#+ 
    #+#+#+#+#+   #+#        #+#   #+#+# #+#    #+# #+#    #+# 
        ###     ########## ###    ####  ########   ########  
    :::::::::::: ::::    ::::  :::::::::   ::::::::  :::::::::  ::::::::::: :::::::::: :::::::::  
        :+:     +:+:+: :+:+:+ :+:    :+: :+:    :+: :+:    :+:     :+:     :+:        :+:    :+: 
        +:+     +:+ +:+:+ +:+ +:+    +:+ +:+    +:+ +:+    +:+     +:+     +:+        +:+    +:+ 
        +#+     +#+  +:+  +#+ +#++:++#+  +#+    +:+ +#++:++#:      +#+     +#++:++#   +#++:++#:  
        +#+     +#+       +#+ +#+        +#+    +#+ +#+    +#+     +#+     +#+        +#+    +#+ 
        #+#     #+#       #+# #+#        #+#    #+# #+#    #+#     #+#     #+#        #+#    #+# 
    ########### ###       ### ###         ########  ###    ###     ###     ########## ###    ###
    """
        return ascii_art


def main():
    os.system("cls")
    with CustomEnvironment():
        processor = FileProcessor(num_processes=10)
        processor.crawl_root()


if __name__ == "__main__":
    main()
