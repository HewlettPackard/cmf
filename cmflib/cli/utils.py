def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"

