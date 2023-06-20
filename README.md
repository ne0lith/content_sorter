# Venus Importer



    :::     ::: :::::::::: ::::    ::: :::    :::  ::::::::  
    :+:     :+: :+:        :+:+:   :+: :+:    :+: :+:    :+: 
    +:+     +:+ +:+        :+:+:+  +:+ +:+    +:+ +:+        
    +#+     +:+ +#++:++#   +#+ +:+ +#+ +#+    +:+ +#++:++#++ 
    +#+     +#+ +#+        +#+  +#+#+# +#+    +#+        +#+ 
     +#+#+#+#+  #+#        #+#   #+#+# #+#    #+# #+#    #+# 
        ###     ########## ###    ####  ########   ########  
    ::::::::::: ::::     :::: :::::::::   ::::::::  ::::::::: ::::::::::: :::::::::: :::::::::  
        :+:     +:+:+: :+:+:+ :+:    :+: :+:    :+: :+:    :+:    :+:     :+:        :+:    :+: 
        +:+     +:+ +:+:+ +:+ +:+    +:+ +:+    +:+ +:+    +:+    +:+     +:+        +:+    +:+ 
        +#+     +#+  +:+  +#+ +#++:++#+  +#+    +:+ +#++:++#:     +#+     +#++:++#   +#++:++#:  
        +#+     +#+       +#+ +#+        +#+    +#+ +#+    +#+    +#+     +#+        +#+    +#+ 
        #+#     #+#       #+# #+#        #+#    #+# #+#    #+#    #+#     #+#        #+#    #+# 
    ########### ###       ### ###         ########  ###    ###    ###     ########## ###    ###



This script is designed to help me effectively manage and organize my content by automatically sorting and naming it in a way that aligns with my personal preferences.

## Installation

Currently, there is no requirements.txt file available for this project. Regrettably, the pipreqs tool is broken in my environment, and I haven't pursued troubleshooting it yet. Therefore, you will need to manually run and install the required dependencies yourself.

Please take the necessary steps to identify and install the dependencies required for this project.

## What To Change
### config.yaml


```yaml
root_dir: "D:/Content/ISOs"
completion_json: "D:/Content/index.json"
history_file: "D:/Content/history/history.json"
protected_models:
  - "darshelle stevens"
  - "jessica nigri"
protected_dirs:
  - "sorted"
  - "corrupted"
```

### Locations of completion_json and history_file
These files can exist wherever you prefer.

### Folder Structure for Compatibility
To ensure compatibility with this script, it is crucial to organize your folder structure as follows:

```
D:\
└── Content\
    └── ISOs\
        ├── ashlie lotus\
        ├── amilia onyx\
        ├── angela white\
        └── angie varona\
```

### Understanding protected_models and protected_dirs

In this script, the concepts of `protected_models` and `protected_dirs` play a vital role in controlling the file processing behavior. Let's explore how these two lists work:

#### protected_models:
The `protected_models` list consists of the first-level subdirectories (model folders) located within the `root_dir`. By adding a model folder name to the `protected_models` list (e.g., "angela white" or "amilia onyx"), the script ensures that all files and subdirectories within those protected model folders are ignored during processing. Essentially, any content within these protected model folders will be excluded from the script's operations.

#### protected_dirs:
On the other hand, the `protected_dirs` list contains general named subdirectories that are not limited to specific model folders. If any model folder contains a subdirectory with a name that matches one of the entries in the `protected_dirs` list, the script will ignore all files and folders within that specific subdirectory. This allows for selective exclusion of content based on these named subdirectories, regardless of the model folder in which they reside.

By utilizing these lists, you gain greater control over which files and directories are processed by the script. The `protected_models` list targets specific model folders, while the `protected_dirs` list enables exclusion based on general named subdirectories within any model folder.

Customize these lists according to your specific requirements to ensure that certain files and directories are excluded from the script's operations, providing a more tailored and focused approach to content management.

## Usage

### Usage Note: Initial Configuration for Testing

Before executing the script in a production environment, it is strongly recommended to set both `is_dry_run` and `is_debug` parameters to `true` on your first run. This allows you to observe and understand the impact the script will have on your libraries without making any actual changes.

By setting `is_dry_run` to `true`, the script will simulate the sorting and renaming operations without modifying any files or directories. This enables you to preview the outcome and evaluate if the script aligns with your expectations.

Similarly, setting `is_debug` to `true` provides additional logging and debugging information during script execution. This helps in identifying any potential issues or inconsistencies in the script's behavior.

Once you have thoroughly reviewed the simulated results and are satisfied with the script's behavior, you can set both `is_dry_run` and `is_debug` parameters to `false` for the actual execution, allowing the script to make the intended changes to your libraries.

Remember, it is crucial to exercise caution and test the script thoroughly before applying it to your valuable content libraries to ensure a smooth and desirable outcome.

Please note that during a dry run simulation, no actual changes should occur to your libraries. However, as the script creator, I have to acknowledge the possibility of overlooking something due to prolonged exposure to the code.

While I have made efforts to ensure the script's accuracy and functionality, I recommend users to thoroughly review the code before running even the simulation. This allows users to familiarize themselves with the script's operations and logic, ensuring a better understanding of the potential outcomes.

### Assumptions and Expected Structure

To ensure the proper functioning of this script, it assumes that your ISOs are organized in a specific manner, [as described above](#folder-structure-for-compatibility). Upon completion of the script, the resulting structure of your ISOs should resemble the following:

```
D:\
└── Content\
    └── ISOs\
        ├── ashlie lotus\
        │   ├── images\
        │   ├── videos\
        │   └── premium\
        ├── amilia onyx\
        │   ├── images\
        │   ├── videos\
        │   └── premium\
        ├── angela white\
        │   ├── images\
        │   ├── videos\
        │   └── premium\
        └── angie varona\
            ├── images\
            ├── videos\
            └── premium\

```

## Limitations 

### Handling of do_renames_lowercase

An important consideration in this script is the treatment of the `do_renames_lowercase` parameter. While the key exists and can be configured, it is essential to note that the script inherently favors lowercase file names. Consequently, even if the `do_renames_lowercase` parameter is set to false, the file names will still be transformed to lowercase.

This behavior ensures consistency within the script and promotes conformity to lowercase naming conventions. It's important to be aware of this behavior when working with the script to avoid unexpected outcomes.

### Handling of do_remove_duplicate_extensions

The `do_remove_duplicate_extensions` feature addresses the issue of multiple occurrences of file extensions within a filename. When enabled, this functionality attempts to remove redundant file extensions from filenames. For example, `filename.jpg.jpg` or `filenamejpg.jpg` would be transformed into `filename.jpg`. Additionally, cases like `0heu75gekk9f1qxw2mztu_source.mp4_thumbsc69fbac96d57811d.jpg` would be modified to `0heu75gekk9f1qxw2mztu_source_thumbsc69fbac96d57811d.jpg`.

However, it is important to note that enabling this feature carries a level of uncertainty. While it aims to streamline filenames by removing duplicate extensions, it may occasionally lead to unexpected results. Therefore, exercising caution is advised when deciding to enable or disable this feature.

### File Renaming with Size Mismatch

During the file import or moving process, it's important to be aware of a specific limitation related to file renaming. If the script encounters a situation where it needs to rename a file due to a size mismatch, a naming convention will be applied. In this scenario, the file name will be modified from `filename.jpg` to `filename_duplicate_n.jpg`, where n represents the number of attempts made to find a unique file name.

While this approach ensures that files are properly renamed to avoid conflicts, it does introduce a potential limitation. The original file name may be altered to include the "duplicate" label and an appended number, which could deviate from the desired naming convention or disrupt the intended file organization.

It is important to consider this limitation when working with the script and be prepared for the possibility of modified file names when mismatches in file sizes occur.

### Improved Import Scheme for Fan Platforms

This project focuses on enhancing the import scheme for popular fan platforms, including Fanhouse, Fansly, Gumroad, and Patreon. Currently, the script imports files based on the presence of specific strings in the file names. However, the file naming conventions for these platforms are unfamiliar, leading to potential limitations.

To overcome this challenge, I am actively refining the import process to provide broader support for various file naming schemes across these platforms. Notably, I have encountered no issues with platforms like OnlyFans and Coomerparty. Additionally, I have implemented a fallback mechanism that references the site name within the file for OnlyFans.

The objective is to ensure a seamless and reliable import experience by accommodating the unique file naming conventions of different fan platforms.

```python
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
```
