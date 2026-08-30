import json

import click
import typing as t
import pandas as pd
from cmflib import cmfquery
from tabulate import tabulate

__all__ = ['query']


def _print_executions_in_stage(cmf_query: cmfquery.CmfQuery, stage_name: str, frmt: str) -> None:
    print('\n')
    print('\n')
    df: pd.DataFrame = cmf_query.get_all_executions_in_stage(stage_name)

    drop_cols = []
    if 'Git_Start_Commit' in df.columns:
        drop_cols.append('Git_Start_Commit')
    if 'Git_End_Commit' in df.columns:
        drop_cols.append('Git_End_Commit')
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True, axis=1)

    if frmt == 'table':
        print(tabulate(df, headers='keys', tablefmt='psql'))
    else:
        print(json.dumps(df.to_dict("records"), indent=4))


def query(mlmd_path: str, pipeline: str, steps: str, frmt: str) -> None:
    cmf_query = cmfquery.CmfQuery(mlmd_path)
    stages: t.List[str] = cmf_query.get_pipeline_stages(pipeline)
    print(stages)

    for name in steps.split(','):
        _print_executions_in_stage(cmf_query, name, frmt)


@click.command()
@click.argument('mlmd_path', required=True, type=str, help='Path to MLMD sqlite store.')
@click.argument('pipeline', required=True, type=str, help='Pipeline name.')
@click.argument('steps', required=True, type=str, help='Comma-separated string of step names.')
@click.argument('format', required=True, type=str, help='Output format (`table`, `json`)')
def query_cli(mlmd_path: str, pipeline: str, steps: str, frmt: str) -> None:
    query(mlmd_path, pipeline, steps, frmt)


if __name__ == '__main__':
    query_cli()
