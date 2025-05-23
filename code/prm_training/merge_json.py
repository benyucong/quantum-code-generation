import os
import json
import argparse
from glob import glob


def find_json_files(directory, exclude_files=None):
    pattern = os.path.join(directory, "**", "*.json")
    json_files = glob(pattern, recursive=True)

    if exclude_files is None:
        exclude_files = set()

    json_files = [f for f in json_files if os.path.abspath(f) not in exclude_files]
    return json_files


def merge_json_files(json_files):
    merged_data = []
    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged_data.append(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file {file}: {e}")
        except Exception as e:
            print(f"Error reading file {file}: {e}")
    return merged_data


def main():
    parser = argparse.ArgumentParser(
        description="Merge all JSON files in a repository into a single JSON file."
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=".",
        help="The root directory to search for JSON files (default is current directory).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="merged.json",
        help="The output file name (default is merged.json).",
    )
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    exclude_files = {output_path}

    json_files = find_json_files(args.directory, exclude_files)
    print(f"Found {len(json_files)} JSON files.")

    merged_data = merge_json_files(json_files)

    try:
        with open(args.output, "w", encoding="utf-8") as f_out:
            json.dump(merged_data, f_out, indent=4)
        print(f"Merged JSON saved to {args.output}")
    except Exception as e:
        print(f"Error writing to {args.output}: {e}")


if __name__ == "__main__":
    main()
