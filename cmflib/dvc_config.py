import os
import subprocess


class dvc_config:
    @staticmethod
    def get_dvc_config():
        result = subprocess.run(["dvc", "config", "-l"], capture_output=True, text=True)
        config_list = result.stdout.split("\n")
        config_list.pop(-1)
        config_dict = {}
        for item in config_list:
            item_list = item.split("=")
            config_dict[item_list[0]] = item_list[1]
        if config_dict["core.remote"] == "minio":
            return (
                config_dict["remote.minio.endpointurl"],
                config_dict["remote.minio.access_key_id"],
                config_dict["remote.minio.secret_access_key"],
            )
        elif config_dict["core.remote"] == "myremote":
            return config_dict["remote.myremote.url"]
        else:
            pass


def main():
    dvc_config.get_dvc_config()


if __name__ == "__main__":
    main()
