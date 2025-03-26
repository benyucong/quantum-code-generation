import os
import random

VALID_OPTIMIZATION_TYPES = {"VQE", "QAOA", "ADAPTIVE"}

def parse_filename(filename: str):
    if not filename.endswith(".json"):
        return None, None
    if "_OptimizationType." not in filename:
        return None, None
    parts = filename.split("_OptimizationType.")
    if len(parts) != 2:
        return None, None
    problem_type = parts[0]
    second_part = parts[1]
    sub_parts = second_part.split("_", 1)
    if len(sub_parts) < 2:
        return None, None
    optimization_type = sub_parts[0]
    if optimization_type not in VALID_OPTIMIZATION_TYPES:
        return None, None
    return problem_type, optimization_type

def sample_files(folder: str, target_problem: str, sample_size: int, target_optimization: str = None, dry_run: bool=False):
    matching_files = []
    for filename in os.listdir(folder):
        problem_type, optimization_type = parse_filename(filename)
        if problem_type is None or optimization_type is None:
            continue
        if problem_type != target_problem:
            continue
        if target_optimization is not None and optimization_type != target_optimization:
            continue
        if problem_type == target_problem:
            matching_files.append(filename)
    
    total = len(matching_files)
    print(f"Found {total} files for problem type '{target_problem}' in folder '{folder}'.")
    if total <= sample_size:
        print(f"Total files ({total}) is less than or equal to the sample size ({sample_size}). Nothing to delete.")
        return

    sampled_files = set(random.sample(matching_files, sample_size))
    print(f"Randomly selected {sample_size} file(s) to keep.")

    files_to_delete = [f for f in matching_files if f not in sampled_files]
    print(f"Deleting {len(files_to_delete)} file(s)...")
    for filename in files_to_delete:
        file_path = os.path.join(folder, filename)
        if dry_run:
            print(f"[Dry run] Would delete: {file_path}")
        else:
            os.remove(file_path)
            print(f"Deleted: {file_path}")

def main():
    FOLDER = "out/"
    PROBLEM = "matching"
    SAMPLE_SIZE = 1000
    DRY_RUN = False
    
    sample_files(FOLDER, PROBLEM, SAMPLE_SIZE, target_optimization="VQE", dry_run=DRY_RUN)

if __name__ == "__main__":
    main()
