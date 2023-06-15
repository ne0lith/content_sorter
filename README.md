# Venus Importer



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



This script is designed to help me effectively manage and organize my content by sorting and naming it in a way that aligns with my personal preferences.

## Installation

Currently, there is no requirements.txt file available for this project. Regrettably, the pipreqs tool is broken in my environment, and I haven't pursued troubleshooting it yet. Therefore, you will need to manually run and install the required dependencies yourself.

Please take the necessary steps to identify and install the dependencies required for this project.

## What To Change
### config.yaml


```yaml
root_dir: "D:/Content/ISOs"
completion_json: "D:/Content/index.json"
history_file: "D:/Content/history/history.json"
```

### Locations of completion_json and history_file
These files can exist wherever you prefer.

### Folder Structure for Compatibility
To ensure ompatibility with this script, it is crucial to organize your folder structure as follows:

```
D:\
└── Content\
    └── ISOs\
        ├── ashlie lotus\
        ├── amilia onyx\
        ├── angela white\
        └── angie varona\
```

## Usage

### Assumptions and Expected Structure

To ensure the proper functioning of this script, it assumes that your ISOs are organized in a specific manner, as described above. Upon completion of the script, the resulting structure of your ISOs should resemble the following:

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

### Handling of do_renames_lowercase Issue

An important consideration in this script is the treatment of the do_renames_lowercase parameter. While the key exists and can be configured, it is essential to note that the script inherently favors lowercase file names. Consequently, even if the do_renames_lowercase parameter is set to false, the file names will still be transformed to lowercase.

This behavior ensures consistency within the script and promotes conformity to lowercase naming conventions. It's important to be aware of this behavior when working with the script to avoid unexpected outcomes.

### Improved Import Scheme for Fan Platforms

This project focuses on enhancing the import scheme for popular fan platforms, including Fanhouse, Fansly, Gumroad, and Patreon. Currently, the script imports files based on the presence of specific strings in the file names. However, the file naming conventions for these platforms are unfamiliar, leading to potential limitations.

To overcome this challenge, I am actively refining the import process to provide broader support for various file naming schemes across these platforms. Notably, I have encountered no issues with platforms like OnlyFans and Coomerparty. Additionally, I have implemented a fallback mechanism that references the site name within the file for OnlyFans.

The objective is to ensure a seamless and reliable import experience by accommodating the unique file naming conventions of different fan platforms. I appreciate any interest and would love if anyone decided to contribute to the project and provide feedback to enhance the functionality and usability of the import scheme.

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
