def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"


def create_cmf_config(file_name: str, cmf_server_ip: str):
    fp = open(file_name, "w")
    fp.write(f"cmf-server-ip = {cmf_server_ip}")
    fp.close()

def main():
    create_cmf_config("./.cmfconfig", "http://127.0.0.1:80")


if __name__ == "__main__":
    main()
