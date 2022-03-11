import pandas as pd
import sys
from datetime import datetime
from uuid import uuid4
from cmflib import cmfquery
from tabulate import tabulate

repo_path = sys.argv[1]
query = cmfquery.CmfQuery(repo_path)
stages = query.get_pipeline_stages("Test-env")
print(stages)

print("\n")
print("\n")
df = query.get_all_executions_in_stage('Prepare')
print(df)
df.drop(columns=['Git_Start_Commit','Git_End_Commit'], inplace=True, axis = 1)
print(tabulate(df, headers='keys', tablefmt='psql'))

print("\n")
print("\n")

df = query.get_all_executions_in_stage('Featurize')
df.drop(columns=["Git_Start_Commit","Git_End_Commit"], inplace=True, axis = 1)
print(tabulate(df, headers='keys', tablefmt='psql'))

print("\n")
print("\n")

df = query.get_all_executions_in_stage('Train')
df.drop(["Git_Start_Commit","Git_End_Commit"], inplace=True, axis = 1)
print(tabulate(df, headers='keys', tablefmt='psql'))
print("\n")

print("\n")
df = query.get_all_executions_in_stage('Train')
df.drop(["Git_Start_Commit","Git_End_Commit"], inplace=True, axis = 1)
print(tabulate(df, headers='keys', tablefmt='psql'))

print("\n")
print("\n")
df = query.get_all_executions_in_stage('Evaluate')
df.drop(["Git_Start_Commit","Git_End_Commit"], inplace=True, axis = 1)
print(tabulate(df, headers='keys', tablefmt='psql'))
