import os

def is_git_repo(path):
    git_dir = os.path.join(path, '.git')
    result = os.path.exists(git_dir) and os.path.isdir(git_dir)
    if result:
        return f"A Git repository already exists in {subfolder_path}."
    else:
        return
