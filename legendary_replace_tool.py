"""
Creates a skeleton for any project of your choice provided you give a template.
This is done by copying the template then replacing the tags in them,
as according to the tags_template.json you defined.

Current default template is just an example, as I couldn't actually put the
real files I used it on on GitHub, but while this script is quite straightforward
and not very complex, it is quite useful when creating new services and such.

- HOW TO USE -
Choose a template for your source files (source_code_templates)
Make a template for your tags (you can modify
                               tags_templates/tags_template.json if you're lazy)
Choose an output directory.
Done.

-o for output directory
-s for source directory (template for code)
-t for tags template file (template for tags -> words)

--REVERSE to create a source code template from a finished product
(reciprocal operation to the normal usage of legendary_replace_tool)

None of the tags can have the same value if you want
a good template from using --REVERSE

As many templates have the same value for several keys
(happens if there's 1 word only), you might just not get
a good template back. Manual revision is advised.

(i.e. tags_template_EXAMPLE_1 can use --REVERSE to get the original template
      back, but tags_template_EXAMPLE_2 cannot, as too many tags have the
      same value, namely "example" or "examples")
"""
import json
import errno
import os
import stat
import argparse
import shutil

# Argument management
script_abspath = os.path.abspath(__file__)
script_dir_path = os.path.dirname(script_abspath)

DEFAULT_OUT = os.path.join(script_dir_path, "GENERATED_OUTPUT")

DEFAULT_TAGFILE_LOCATION = os.path.join("tags_templates",
                                        "tags_template.json")
DEFAULT_TAGS = os.path.join(script_dir_path, DEFAULT_TAGFILE_LOCATION)

DEFAULT_SOURCEFILE_LOCATION = os.path.join("source_code_templates",
                                            "legendary_template_default")
DEFAULT_SOURCE = os.path.join(script_dir_path, DEFAULT_SOURCEFILE_LOCATION)

arg_parser = argparse.ArgumentParser(description="Generates a project "
                                                 "from a template, "
                                                 "by replacing tags.")
arg_parser.add_argument("-o", "--out", action="store", default=DEFAULT_OUT,
                        help="specify output destination "
                             "(default: "+DEFAULT_OUT+")")
arg_parser.add_argument("-t", "--tags", action="store", default=DEFAULT_TAGS,
                        help="specify tag template dictionary "
                             "(default: "+DEFAULT_TAGS+")")
arg_parser.add_argument("-s", "--source", action="store",
                        default=DEFAULT_SOURCE,
                        help="specify template code source folder "
                             "(default: "+DEFAULT_SOURCE+")")
arg_parser.add_argument('--REVERSE', action='store_true')

tags_template = {}
tags_sorted_by_longest = []


# Most of the base functions for these were just reused from my thesis,
# a documentation generator called "OzDoc",
# available at https://github.com/AlexeSimon/OzDoc
# Check it out if you feel like it.
# These functions were of course modified to fit the needs of this script.
def parse_args(args=None):
    if args is None:
        return arg_parser.parse_args()
    elif isinstance(args, str):
        return arg_parser.parse_args(args.split())
    else:
        return arg_parser.parse_args(args)


# Courtesy of mgrant at https://stackoverflow.com/a/15824216 for base code
def copy_directory_with_replace(src, dest_raw, ignore=None):
    # Added by pfrenyo: replace templates in filenames
    dest = dest_raw
    for key in tags_sorted_by_longest:
        dest = dest.replace(key, tags_template[key])

    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                copy_directory_with_replace(os.path.join(src, f),
                                            os.path.join(dest, f), ignore)
    else:
        try:
            shutil.copyfile(src, dest)
            # Give same file permissions, mainly useful for executables
            source_file_metadata = os.stat(src)
            os.chmod(dest, source_file_metadata.st_mode)
        except shutil.Error:
            pass


# Recursively replaces tags in files and directories, including file names.
def recursive_replace(basepath, reverse=False):
    for filename in os.listdir(basepath):
        filepath = os.path.join(basepath, filename)

        if ".DS_Store" in filename\
           or ".idea" in filename\
           or "__pycache__" in filename:
            # Jetbrains or Python files, ignore. This avoids stdout spam.
            continue

        if os.path.isdir(filepath):
            recursive_replace(filepath, reverse)
        else:
            for key in tags_sorted_by_longest:
                try:
                    with open(filepath, "rt") as f:
                        data = f.read()
                        if reverse:
                            data = data.replace(tags_template[key], key)
                        else:
                            data = data.replace(key, tags_template[key])

                    with open(filepath, "wt") as f:
                        f.write(data)
                except UnicodeDecodeError:
                    print("Could not apply recursive_replace to binary file: "
                          + filepath)


if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists(args.out):
        os.makedirs(args.out)

    with open(args.tags, "r") as f:
        tags_template = json.loads(f.read())

    # The following is mainly useful when working with REVERSE=True, but does
    # no harm in actual use (and is useful if someone reverse tag and value
    # in the json)
    tags_sorted_by_longest = sorted(tags_template,
                                    key=lambda k: len(k),
                                    reverse=True) if not args.REVERSE \
        else sorted(tags_template,
                    key=lambda k: len(tags_template[k]),
                    reverse=True)

    if args.source != args.out:
        copy_directory_with_replace(args.source, args.out)

    recursive_replace(args.out, args.REVERSE)
