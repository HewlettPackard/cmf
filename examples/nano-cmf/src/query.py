import click
import typing as t
import pandas as pd
from cmflib.cmfquery import CmfQuery
from tabulate import tabulate

__all__ = ['query']


def _print_executions_in_stage(cmf_query: CmfQuery, stage_name: str) -> None:
    print('\n')
    print('\n')
    df: pd.DataFrame = cmf_query.get_all_executions_in_stage(stage_name)
    df.drop(columns=['Git_Start_Commit', 'Git_End_Commit'], inplace=True, axis=1)
    print(tabulate(df, headers='keys', tablefmt='psql'))


def query(mlmd_path: str) -> None:
    cmf_query = CmfQuery(mlmd_path)
    stages: t.List[str] = cmf_query.get_pipeline_stages("nano-cmf")
    print(stages)

    for stage in stages:
        _print_executions_in_stage(cmf_query, stage)


@click.command()
@click.argument('mlmd_path', required=True, type=str)
def query_cli(mlmd_path: str):
    query(mlmd_path)


if __name__ == '__main__':
    query_cli()
