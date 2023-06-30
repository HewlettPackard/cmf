from cmflib import cli


def mt_push(self, pipeline_name, file_name, execution_id: int = 0):
    cli_args = cli.parse_args(
            [
               "metadata",
               "push",
               "-p",
               "active_learning_demo"
            ]
           )
    # print(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg




def mt_pull(self):
    cli_args = cli.parse_args(
            [
               "metadata",
               "pull",
               "-p",
               "active_learning_demo"
            ]
           )
    print(cli_args)



def arti_push(self):
    cli_args = cli.parse_args(
            [
               "artifact",
               "push",
            ]
           )
    print(cli_args)


def arti_pull(self):
    cli_args = cli.parse_args(
            [
               "artifact",
               "pull",
            ]
           )
    print(cli_args)


def cmf_cmd_init(self, artifact_type: str): 
    cli_args = cli.parse_args(
            [
               "init",
               artifact_type
            ]
           )
    print(cli_args)
