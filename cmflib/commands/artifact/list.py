###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import argparse
import os
import pandas as pd
import textwrap

from tabulate import tabulate
from cmflib.cli.command import CmdBase
from cmflib import cmfquery
from cmflib.dvc_wrapper import dvc_get_config

class CmdArtifactsList(CmdBase):
    def update_dataframe(self, df, is_long):
        # This function used to modify datafram to fit inside table   
        if is_long:
            # If the option is long then all columns need to take
            updated_columns = ["id", "name"] + [ col for col in df.columns if not (col == "id" or col == "name")]
            df = df[updated_columns]
        else:
            # If the option is not long then few selective columns will take with custom_properties, 
            # if number of column is greater than 5 then it only use 5 columns. 
            updated_columns = ["id", "name"] + [ col for col in df.columns if col.startswith('custom_properties_')]
            df = df[updated_columns]
            if len(df.columns) > 5:
                df=df.iloc[:,:5]
        return df
    
    def display_table(self, df, char_size, is_custom_prop):
        if is_custom_prop:
            # Replacing column name 
            # For eg: custom_properties_avg_prec ---> avg_prec  
            df = df.rename(columns = lambda x: x.replace("custom_properties_", "") if x.startswith("custom_properties_") else x)
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=char_size) if isinstance(x, str) else x)

        total_records = len(df)
        start_index = 0  # Initialize outside the loop

        while True:
            end_index = start_index + 20
            records_per_page = df.iloc[start_index:end_index]

            table = tabulate(
                records_per_page,
                headers=df.columns,
                tablefmt="grid",
                showindex=False,
            )
            print(table)

            # Check if we've reached the end
            if end_index >= total_records:
                print("\nEnd of records.")
                break

            # Ask the user for input
            user_input = input("Press Enter to see more or 'q' to quit: ").strip().lower()
            if user_input == 'q':
                break
            
            # Update indices for the next page
            start_index = end_index 


    def search_artifact(self, df):
        matched_ids = []
        for index, row in df.iterrows():
            # the artifact name is this format artifacts/features/test.pkl:12345heyewuswjwi
            # we compare whether the user given artifact name is inbetween following
            # 1. artifacts/features/test.pkl 2. test.pkl

            # print(row['name'])
            # in case of multiple same names--> we need to store all artifcat ids
            artifact_name =  row['name'].split(":")[0]
            if self.args.artifact_name == artifact_name:
                matched_ids.append(row['id'])
            elif self.args.artifact_name == artifact_name.split('/')[-1]:
                matched_ids.append(row['id'])
        
        # the matched_ids is empty 
        if len(matched_ids) != 0:
            return matched_ids
        return -1

    def run(self):
        # cmf/dvc configured or not
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        
        current_directory = os.getcwd()
        # default path for mlmd file name
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."

        # Creating cmfquery object
        query = cmfquery.CmfQuery(mlmd_file_name)

        df = query.get_all_artifacts_by_context(self.args.pipeline_name)
        if df.empty:
            return "Pipeline name doesn't exists..."
        else:
            if self.args.artifact_name:
                artifact_ids = self.search_artifact(df)
                if(artifact_ids != -1):
                    # If multiple artifact name exists with same name 
                    for artifact_id in artifact_ids:
                        # Extracting data based on ID
                        filtered_data = df.loc[df['id'] == artifact_id]
                        
                        filtered_data = self.update_dataframe(filtered_data, True)
                        
                        for col in filtered_data.select_dtypes(include=['object']).columns:
                            filtered_data[col] = filtered_data[col].apply(lambda x: textwrap.fill(x, width=30) if isinstance(x, str) else x)

                        # setting default index as a id
                        filtered_data.set_index("id", inplace=True)
                        # T is used to transpose the dataframe
                        # Resetting index and assigning name to that index
                        filtered_data = filtered_data.T.reset_index()
                        filtered_data.columns.values[0] = 'id'

                        table = tabulate(
                            filtered_data,
                            headers=filtered_data.columns,
                            tablefmt="grid",
                            showindex=False,
                        )
                        print(table)
                        print()
                        user_input = input("Press Enter to see more records if exists or 'q' to quit: ").strip().lower()
                        if user_input == 'q':
                            break
                    return "End of records.."
                else:
                    return "Artifact name does not exist.."

        if self.args.long:
            df = self.update_dataframe(df, True)
            if len(df.columns) > 7:
                df=df.iloc[:,:7]
            
            # Replacing column name 
            # For eg: custom_properties_avg_prec ---> avg_prec  
            self.display_table(df, 14, True)
        else:
            df = self.update_dataframe(df, False)
            self.display_table(df, 25, True)
        return "Done"

def add_parser(subparsers, parent_parser):
    ARTIFACT_LIST_HELP = "Display list of artifact as present in current mlmd"

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display artifact list",
        help=ARTIFACT_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name", 
        required=True,
        help="Specify pipeline name.", 
        metavar="<pipeline_name>", 
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>",
    )

    parser.add_argument(
        "-a", 
        "--artifact_name", 
        help="Specify artifact name.", 
        metavar="<artifact_name>",
    )

    parser.add_argument(
        "-l", 
        "--long", 
        action='store_true',
        help="Display detailed summary of artifact",
    )

    parser.set_defaults(func=CmdArtifactsList)