import os
import re
import sys
import json
import time
import uuid
import yaml
import shutil
import codecs
import fnmatch
import platform
import datetime
import builtins
import traceback
from PIL import Image
from tqdm import tqdm
from functools import partial
from multiprocessing import Pool
from pathlib import Path, WindowsPath


class CustomEnvironment:
    def __init__(self):
        self.original_print = builtins.print
        self.original_input = builtins.input
        self.original_write = tqdm.write
        sys.stdout.write("\033[?25l")

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
        modified_prompt = "    " + str(prompt)
        return self.original_input(modified_prompt)

    def custom_write(self, s, *args, **kwargs):
        modified_s = "    " + str(s)
        self.original_write(modified_s, *args, **kwargs)

    def restore(self):
        builtins.print = self.original_print
        builtins.input = self.original_input
        tqdm.write = self.original_write
        sys.stdout.write("\033[?25h")


class Config:
    def __init__(self):
        self.config_path = Path(__file__).parent / "config.yaml"
        self.load_config()

    def load_config(self):
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def get_value(self, key):
        value = self.config.get(key)
        if key in ["root_dir", "completion_json", "history_file"]:
            value = Path(value)
        return value

    def set_value(self, key, value):
        self.config[key] = value


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
        history_file_backup = self.history_file.with_suffix(".bak")

        if self.history_file.exists():
            if not history_file_backup.exists():
                shutil.copy(self.history_file, history_file_backup)
            else:
                if (
                    self.history_file.stat().st_size
                    > history_file_backup.stat().st_size
                ):
                    shutil.copy(self.history_file, history_file_backup)


class VideoConverter:
    def __init__(self):
        self.conversion_success = False
        self.is_mp4 = False

    def copy(self, input_file, output_file):
        import ffmpeg
        import subprocess

        try:
            input_stream = ffmpeg.input(str(input_file))
            output_stream = ffmpeg.output(
                input_stream, str(output_file), vcodec="copy", acodec="copy"
            )
            cmd = ffmpeg.compile(output_stream, overwrite_output=True)
            with subprocess.Popen(
                cmd, stderr=subprocess.PIPE, universal_newlines=True
            ) as p:  # noqa F841
                while True:
                    total_time = 0
                    tqdm.write(f"           {total_time}", end="\r")
                    time.sleep(0.5)
                    total_time += 0.5
                    if self.is_valid_mp4(output_file):
                        self.conversion_success = True
                        self.is_mp4 = True
                        break
                    else:
                        self.conversion_success = False
                        self.is_mp4 = False

        except ffmpeg.Error as e:
            tqdm.write(f"An error occurred during video copying of {input_file}")
            tqdm.write(e.stderr + "\n")
            self.conversion_success = False
            self.is_mp4 = False

    def convert(self, input_file, output_file):
        import ffmpeg
        import subprocess

        try:
            input_stream = ffmpeg.input(str(input_file))
            output_stream = ffmpeg.output(
                input_stream,
                str(output_file),
                **self.get_output_codec_options(input_file),
            )
            cmd = ffmpeg.compile(output_stream, overwrite_output=True)
            with subprocess.Popen(
                cmd, stderr=subprocess.PIPE, universal_newlines=True
            ) as p:  # noqa F841
                while True:
                    total_time = 0
                    tqdm.write(f"           {total_time}", end="\r")
                    time.sleep(0.5)
                    total_time += 0.5
                    if self.is_valid_mp4(output_file):
                        self.conversion_success = True
                        self.is_mp4 = True
                        break
                    else:
                        self.conversion_success = False
                        self.is_mp4 = False

        except ffmpeg.Error as e:
            tqdm.write(f"An error occurred during video conversion of {input_file}")
            tqdm.write({e.stderr} + "\n")
            self.conversion_success = False
            self.is_mp4 = False

    def copy_or_convert(self, input_file, output_file):
        self.conversion_success = False
        self.is_mp4 = False

        input_file_path = Path(input_file)
        output_file_path = Path(output_file)

        ext = input_file_path.suffix.lower()[1:]

        if ext in ["avi", "m4v", "mkv", "mov", "mpeg", "ts", "wmv"]:
            self.copy(input_file_path, output_file_path)
            if not self.conversion_success:
                self.convert(input_file_path, output_file_path)
        else:
            tqdm.write(f"Unsupported input file format: {ext}\n")

    def is_valid_mp4(self, file_path):
        import subprocess

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_format",
                    "-of",
                    "json",
                    str(file_path),
                ],
                capture_output=True,
            )
            output = result.stdout.decode("utf-8")
            json_output = json.loads(output)
            if "format" in json_output:
                format_info = json_output["format"]
                if (
                    "format_name" in format_info
                    and format_info["format_name"] == "mov,mp4,m4a,3gp,3g2,mj2"
                ):
                    return True

        except Exception as e:
            tqdm.write(
                f"An error occurred while checking the validity of the MP4 file: {e}\n"
            )

        return False

    def get_output_codec_options(self, input_file):
        ext = Path(input_file).suffix.lower()[1:]

        if ext == "avi":
            return {"vcodec": "libx264", "acodec": "aac"}
        elif ext == "m4v":
            return {"vcodec": "copy", "acodec": "copy"}
        elif ext == "mkv":
            return {"vcodec": "copy", "acodec": "copy"}
        elif ext == "mov":
            return {"vcodec": "copy", "acodec": "copy"}
        elif ext == "mpeg":
            return {"vcodec": "mpeg2video", "acodec": "copy"}
        elif ext == "ts":
            return {"vcodec": "copy", "acodec": "copy"}
        elif ext == "wmv":
            # return {"vcodec": "wmv2", "acodec": "wmav2"}
            return {"vcodec": "libx264", "acodec": "aac"}

        return {}


class FileProcessor:
    def __init__(self, num_processes) -> None:
        self.num_processes = num_processes

        self.config = Config()
        for key in self.config.config.keys():
            setattr(self, key, self.config.get_value(key))

        self.history_instance = History(self.history_file)

        if self.do_video_converts:
            self.converter_instance = VideoConverter()

        self.progress_bar = None
        self.file_count = 0
        self.update_interval = 850

        self.excluded_dirs = self.protected_dirs + [
            self.root_dir / dir for dir in self.protected_models
        ]

        self.result_dict = dict()
        self.videos_to_convert = list()
        self.images_to_convert = list()
        self.files_touched = list()

        print("\n" + self.get_ascii_art() + "\n\n")
        print(f"Version: {self.version}")
        print(f" Author: {self.author}\n\n")

        if self.output_attributes:
            self.output_launch_attributes()
            print()

    def process_root(self) -> None:
        start_time = time.time()

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

        self.history_instance.save_history()
        self.export_result_dict(str(self.completion_json), self.result_dict)

        total_time = time.time() - start_time

        if len(self.files_touched) > 0:
            print()
        print("-----------------------------------\n\n")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Total files: {self.file_count}\n\n")

        if self.videos_to_convert:
            self.output_conversion_leftovers(self.videos_to_convert, "videos")

        if self.images_to_convert:
            if self.videos_to_convert:
                print()
            self.output_conversion_leftovers(self.images_to_convert, "images")

        print()
        input("Press any key to exit...")
        print()

    def process_file(self, file_path) -> None:
        if self.do_converts:
            self._process_image_converts(file_path)

        if self.do_video_converts:
            self._process_video_converts(file_path)

        if self.do_renames:
            self._process_lowercase_filename(file_path)
            self._process_clean_duplicate_extensions(file_path)

        if self.do_imports:
            self._process_premium_file_imports(file_path)
            self._process_loose_file_imports(file_path)

        self._process_conversion_leftovers(file_path)

        self._process_add_to_result_dict(file_path)

        self.file_count += 1

        if self.file_count % self.update_interval == 0:
            self.progress_bar.update(self.update_interval)

    def process_directory(self, dir_path, partial_func) -> None:
        for entry in os.scandir(dir_path):
            if entry.is_dir():
                skip_directory = False
                for exclude_dir in self.excluded_dirs:
                    if isinstance(exclude_dir, str):
                        if fnmatch.fnmatch(entry.name, exclude_dir):
                            skip_directory = True
                            break
                    elif isinstance(exclude_dir, Path):
                        if entry.path.startswith(str(exclude_dir)):
                            skip_directory = True
                            break

                if skip_directory:
                    if self.is_debug:
                        tqdm.write(f"Skipping {entry.path}\n")
                    continue

                if self.do_renames_lowercase:
                    if entry.name != entry.name.lower():
                        tqdm.write(f"Incorrect casing: {entry.path}\n")

                self.process_directory(entry.path, partial_func)

            if entry.is_file():
                if ".part" in Path(entry).suffix:
                    if self.is_debug:
                        tqdm.write(f"Skipping {entry.path}\n")

                    continue

                partial_func(Path(entry.path))

    def output_launch_attributes(self) -> None:
        attributes = vars(self)
        exclude_keys = set(["ascii_art", "config", "exclude_dirs", "excluded_dirs"])

        for key, value in attributes.items():
            if key in exclude_keys:
                continue

            value_type = type(value).__name__

            if (
                (value_type in ["str", "bool", "WindowsPath"] and value)
                or (value_type == "int" and value != 0)
                or (value_type == "dict" and len(value) > 0)
                or (value_type == "list" and len(value) > 0)
            ):
                if value_type == "list" and any(
                    isinstance(item, WindowsPath) for item in value
                ):
                    value = [str(item).replace("\\", "/") for item in value]

                print(f"{key}: {value} ({value_type})")

        print()
        input("Press Enter to continue...")

    def output_conversion_leftovers(self, items_to_convert, item_type) -> None:
        amount_string = (
            f"{item_type.capitalize()} to convert: ({len(items_to_convert)})"
        )
        print(amount_string)
        print("-" * len(amount_string))
        items_by_extension = {}
        for item in items_to_convert:
            item_path = str(item)
            extension = os.path.splitext(item_path)[1][1:]
            if extension not in items_by_extension:
                items_by_extension[extension] = []
            items_by_extension[extension].append(item_path)

        sorted_items = sorted(
            items_to_convert, key=lambda x: os.path.splitext(str(x))[-1][1:]
        )
        sorted_items_by_extension = dict(
            sorted(items_by_extension.items(), key=lambda item: item[0])
        )

        for extension, items in sorted_items_by_extension.items():
            print()
            print(f"Extension: .{extension}")
            [print(item_path) for item_path in sorted_items if str(item_path) in items]

    def _process_image_converts(self, file_path) -> None:
        if not self.do_image_converts:
            return

        input_path = Path(file_path)

        if input_path.suffix.lower() in self.convertable_image_extensions:
            self.convert_image_to_jpg(input_path)
            if not self.is_dry_run:
                file_path = input_path.with_suffix(".jpg")

    def _process_video_converts(self, file_path) -> None:
        if not self.do_video_converts:
            return

        input_path = Path(file_path)
        if input_path.suffix.lower() in self.convertable_video_extensions:
            self.convert_video_to_mp4(input_path)

    def _process_lowercase_filename(self, file_path) -> None:
        if not self.do_renames_lowercase:
            return

        input_path = Path(file_path)

        if input_path.name != input_path.name.lower():
            output_path = input_path.parent / input_path.name.lower()
            self.rename_file(input_path, output_path)
            if not self.is_dry_run:
                file_path = output_path

    def _process_clean_duplicate_extensions(self, file_path) -> None:
        if not self.do_clean_duplicate_extensions:
            return

        if not self.is_duplicate_extensions(file_path):
            return

        input_path = Path(file_path)

        output_name = self.get_clean_duplicate_extensions(input_path.name)
        output_path = input_path.parent / output_name

        if output_path != file_path:
            self.rename_file(input_path, output_path)
            if not self.is_dry_run:
                file_path = output_path

    def _process_premium_file_imports(self, file_path) -> None:
        if not self.do_premium_imports:
            return

        if not self.is_premium_file(file_path):
            return

        if self.is_social_media(file_path):
            return

        model_premium_directory = self.get_model_premium_directory(file_path)

        if model_premium_directory == file_path.parent:
            return

        if not self.is_dry_run:
            if not model_premium_directory.exists():
                model_premium_directory.mkdir()

        input_path = Path(file_path)
        output_path = model_premium_directory / file_path.name

        self.rename_file(input_path, output_path)
        if not self.is_dry_run:
            file_path = output_path

    def _process_loose_file_imports(self, file_path) -> None:
        if not self.do_loose_file_imports:
            return

        model_dir = self.get_model_name_from_file_path(file_path)
        model_dir = self.root_dir / model_dir

        if model_dir == file_path.parent and any(
            file_path.suffix in filetypes for filetypes in self.valid_filetypes.values()
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
                else:
                    tqdm.write(f"Would create {subdir_path}\n")

            input_path = Path(file_path)
            output_path = subdir_path / file_path.name

            self.rename_file(input_path, output_path)
            if not self.is_dry_run:
                file_path = output_path

    def _process_conversion_leftovers(self, file_path) -> None:
        file_path = Path(file_path)

        if (
            file_path.suffix.lower() in self.valid_filetypes["images"]
            and file_path.suffix.lower() not in self.goal_image_extensions
            and file_path.exists()
        ):
            self.images_to_convert.append(file_path)

        if (
            file_path.suffix.lower() in self.valid_filetypes["videos"]
            and file_path.suffix.lower() not in self.goal_video_extensions
            and file_path.exists()
        ):
            self.videos_to_convert.append(file_path)

    def _process_add_to_result_dict(self, file_path) -> None:
        file_path = Path(file_path)

        relative_path = file_path.relative_to(self.root_dir)
        key = str(relative_path.parts[0])
        list_type = str(relative_path.parent.name)
        value = str(relative_path.name)

        if key not in self.result_dict:
            self.result_dict[key] = [{list_type: [value]}]
        else:
            for item in self.result_dict[key]:
                if list_type in item:
                    item[list_type].append(value)
                    break
            else:
                self.result_dict[key].append({list_type: [value]})

    def is_empty_directory(self, path: Path) -> bool:
        path = Path(path)

        if not self.is_valid_path(path, expect="directory"):
            raise ValueError("Invalid directory path")

        if any(item.is_file() for item in path.iterdir()):
            return False

        for item in path.iterdir():
            if item.is_dir():
                if not self.is_empty_directory(item):
                    return False

        return True

    def is_valid_path(self, path: Path, expect=None) -> bool:
        path = Path(path)

        if expect not in ["file", "directory"]:
            tqdm.write(f"Invalid expect value: {expect}. Must be 'file' or 'directory'")
            return False

        if not path.exists():
            return False

        if expect == "file":
            return path.is_file()
        elif expect == "directory":
            return path.is_dir()

        return False

    def is_social_media(self, file_path: Path) -> bool:
        def is_instagram_or_twitter_file(file_path: Path):
            protected_suffixes = [".jpg", ".jpeg", ".mp4"]
            instagram_twitter_file_pattern = re.compile(
                r".*(?:_n\.(?:jpe?g|mp4)|-img1\.(?:jpe?g|mp4)|-vid1\.mp4|_video_dashinit\.mp4)$"
            )

            pattern = instagram_twitter_file_pattern
            if any(suffix in file_path.suffix for suffix in protected_suffixes):
                if pattern.match(file_path.name):
                    return True

            return False

        return is_instagram_or_twitter_file(file_path)

    def is_premium_file(self, file_path: Path) -> bool:
        def is_coomer_file(file_path) -> bool:
            pattern = r"^[a-fA-F0-9]{64}$"
            return bool(re.match(pattern, file_path.stem))

        def is_fanhouse_file(file_path) -> bool:
            return "fanhouse" in file_path.stem.lower()

        def is_fansly_file(file_path) -> bool:
            return "fansly" in file_path.stem.lower()

        def is_gumroad_file(file_path) -> bool:
            return "gumroad" in file_path.stem.lower()

        def is_onlyfans_file(file_path) -> bool:
            def is_image(file_path) -> bool:
                pattern = r"\d+x\d+_[a-z0-9]{32}"
                return (
                    re.search(pattern, file_path.stem)
                    and file_path.suffix.lower() in self.valid_filetypes["images"]
                )

            def is_video(file_path) -> bool:
                pattern = r"[a-z0-9]{21}(_source|_480p|_720p|_1080p)"
                return (
                    re.search(pattern, file_path.stem)
                    and file_path.suffix.lower() in self.valid_filetypes["videos"]
                )

            return (
                is_image(file_path)
                or is_video(file_path)
                or "onlyfans" in file_path.stem.lower()
            )

        def is_patreon_file(file_path) -> bool:
            return "patreon" in file_path.stem.lower()

        def is_ppv_file(file_path) -> bool:
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

    def is_duplicate_extensions(self, file_path: Path) -> bool:
        file_path = Path(file_path)

        file_name = file_path.name

        parts = file_name.split(".")
        file_stem = ".".join(parts[:-1])

        self.possible_extensions = (
            self.valid_filetypes["videos"] + self.valid_filetypes["images"]
        )

        for ext in self.possible_extensions:
            if ext in file_stem:
                return True

        return False

    def get_unique_file_path(self, file_path: Path) -> Path:
        file_name = file_path.stem.lower()
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

    def get_clean_duplicate_extensions(self, file_path: Path) -> str:
        file_path = Path(file_path)

        file_name = file_path.name

        parts = file_name.split(".")
        actual_ext = parts[-1]
        output_name = ".".join(parts[:-1])

        for ext in self.possible_extensions:
            if ext in output_name:
                output_name = output_name.replace(ext, "")

        output_name = f"{output_name}.{actual_ext}"

        if file_name == output_name:
            return file_name

        return output_name

    def get_model_name_from_file_path(self, file_path: Path) -> str:
        file_model = file_path.parts[file_path.parts.index(self.root_dir.parts[-1]) + 1]

        return file_model

    def get_model_premium_directory(self, file_path: Path) -> Path:
        file_model = self.get_model_name_from_file_path(file_path)
        model_premium_directory = self.root_dir / file_model / self.premium_directory

        return model_premium_directory

    def get_ascii_art(self) -> str:
        ascii_block = """
    :::     ::: :::::::::: ::::    ::: :::    :::  ::::::::  
    :+:     :+: :+:        :+:+:   :+: :+:    :+: :+:    :+: 
    +:+     +:+ +:+        :+:+:+  +:+ +:+    +:+ +:+        
    +#+     +:+ +#++:++#   +#+ +:+ +#+ +#+    +:+ +#++:++#++ 
    +#+     +#+ +#+        +#+  +#+#+# +#+    +#+        +#+ 
     +#+#+#+#+  #+#        #+#   #+#+# #+#    #+# #+#    #+# 
        ###     ########## ###    ####  ########   ########  
    :::::::::::: ::::    ::::  :::::::::   ::::::::  ::::::::: ::::::::::: :::::::::: :::::::::  
        :+:     +:+:+: :+:+:+ :+:    :+: :+:    :+: :+:    :+:    :+:     :+:        :+:    :+: 
        +:+     +:+ +:+:+ +:+ +:+    +:+ +:+    +:+ +:+    +:+    +:+     +:+        +:+    +:+ 
        +#+     +#+  +:+  +#+ +#++:++#+  +#+    +:+ +#++:++#:     +#+     +#++:++#   +#++:++#:  
        +#+     +#+       +#+ +#+        +#+    +#+ +#+    +#+    +#+     +#+        +#+    +#+ 
        #+#     #+#       #+# #+#        #+#    #+# #+#    #+#    #+#     #+#        #+#    #+# 
    ########### ###       ### ###         ########  ###    ###    ###     ########## ###    ###"""

        return ascii_block

    def convert_video_to_mp4(self, file_path: Path) -> None:
        file_path = Path(file_path)

        input_path = file_path
        output_path = file_path.with_suffix(".mp4")

        if ".vid" in file_path.suffix.lower():
            if not self.is_dry_run:
                self.rename_file(file_path, output_path)

            else:
                tqdm.write(" Dry run:")
                tqdm.write(f"Original: {file_path.name}")
                tqdm.write(f"     New: {output_path.name}\n")

            return

        if output_path.exists():
            output_path = self.get_unique_file_path(output_path)

        if not self.is_dry_run:
            tqdm.write(f"    Found: {input_path.name}")
            self.converter_instance.copy_or_convert(input_path, output_path)
            if self.converter_instance.conversion_success:
                if self.converter_instance.is_mp4:
                    tqdm.write(f" Original: {input_path}")
                    tqdm.write(f"      New: {output_path}\n")
                    file_path = output_path
                    if input_path.exists():
                        input_path.unlink()
                        self.files_touched.append(output_path)
                else:
                    tqdm.write(f"Original: {input_path}")
                    tqdm.write("     New: Failed to convert.\n")
                    if output_path.exists():
                        output_path.unlink()
            else:
                tqdm.write(f"Original: {input_path}")
                tqdm.write("     New: Failed to convert.\n")
                if output_path.exists():
                    output_path.unlink()

        else:
            tqdm.write(" Dry run:")
            tqdm.write(f"Original: {input_path}")
            tqdm.write(f"     New: {output_path}\n")

    def convert_image_to_jpg(self, file_path: Path) -> None:
        file_path = Path(file_path)

        if "jpeg" in file_path.suffix.lower():
            output_path = file_path.with_suffix(".jpg")
            self.rename_file(file_path, output_path)
            return

        if file_path.suffix.lower() in [".png", ".jfif"]:
            file_path = Path(file_path)
            if not self.is_dry_run:
                try:
                    image = Image.open(file_path)

                    if image.mode in ["RGBA", "P"]:
                        image = image.convert("RGB")

                    input_path = file_path
                    output_path = file_path.with_suffix(".jpg")
                    output_path = self.get_unique_file_path(output_path)
                    image.save(output_path, "JPEG", quality=100)

                    if output_path.is_file() and output_path.stat().st_size > 0:
                        tqdm.write(f"Original: {file_path}")
                        tqdm.write(f"     New: {output_path}\n")
                        file_path.unlink()
                        self.files_touched.append(output_path)
                    else:
                        tqdm.write(input_path)
                        tqdm.write(
                            "Error occurred during conversion. Original file not deleted.\n"
                        )
                        if output_path.is_file():
                            output_path.unlink()
                except Exception as e:
                    tqdm.write("File:", input_path)
                    tqdm.write(
                        "Error occurred during conversion. Original file not deleted."
                    )
                    tqdm.write(f"Error message: {str(e)}\n")
                    if output_path.is_file():
                        output_path.unlink()
            else:
                tqdm.write(" Dry run:")
                tqdm.write(f"Original: {file_path}")
                tqdm.write(f"     New: {output_path}\n")
        else:
            tqdm.write("File:", file_path)
            tqdm.write("File is not a PNG or JFIF.\n")
            self.images_to_convert.append(file_path)

    def rename_file(self, input_path: Path, output_path: Path) -> None:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if input_path == output_path:
            return

        output_path = output_path.parent / output_path.name.lower()

        if not self.is_valid_path(input_path, expect="file"):
            tqdm.write(f"Invalid file path: {input_path}\n")
            return

        if not self.is_dry_run:
            try:
                input_path.rename(output_path)
                self.history_instance.append_to_history(input_path, output_path)

                tqdm.write(f"Original: {input_path}")
                tqdm.write(f"     New: {output_path}\n")
                self.files_touched.append(output_path)

            except FileExistsError:
                input_size = input_path.stat().st_size
                output_size = output_path.stat().st_size

                if input_size == output_size:
                    input_path.unlink()
                    tqdm.write("File already exists.")
                    tqdm.write(f"Deleted duplicate file: {input_path}\n")
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

        else:
            tqdm.write(" Dry run:")
            tqdm.write(f"Original: {input_path}")
            tqdm.write(f"     New: {output_path}\n")

    def export_result_dict(self, output_path: Path, result_dict=None) -> None:
        with codecs.open(
            output_path, "w", encoding="utf-8", errors="surrogateescape"
        ) as f:
            json.dump(self.result_dict, f, indent=4, ensure_ascii=False)
            f.write("\n")


def main():
    os.system("cls" if platform.system() == "Windows" else "clear")
    with CustomEnvironment():
        processor = FileProcessor(8)
        processor.process_root()


if __name__ == "__main__":
    main()
