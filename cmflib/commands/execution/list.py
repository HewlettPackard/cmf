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
import textwrap
import pandas as pd

from cmflib.cli.command import CmdBase
from cmflib import cmfquery
from tabulate import tabulate
from cmflib.cmf_exception_handling import (
    PipelineNotFound,
    FileNotFound,
    DuplicateArgumentNotAllowed,
    MissingArgument,
    MsgSuccess,
    ExecutionUUIDNotFound
)

class CmdExecutionList(CmdBase):

    def display_table(self, df: pd.DataFrame) -> None:
        """
        Display the DataFrame in a paginated table format with text wrapping for better readability.
        Parameters:
        - df: The DataFrame to display.
        """
        # Rearranging columns
        updated_columns = ["id", "Context_Type", "Execution", "Execution_uuid", "name", "Pipeline_Type", "Git_Repo"] 
        df = df[updated_columns]
        df = df.copy()
       
        # Wrap text in object-type columns to a width of 14 characters.
        # This ensures that long strings are displayed neatly within the table.
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=14) if isinstance(x, str) else x)

        total_records = len(df)
        start_index = 0  

        # Display up to 20 records per page for better readability. 
        # This avoids overwhelming the user with too much data at once, especially for larger mlmd files.
        while True:
            end_index = start_index + 20
            records_per_page = df.iloc[start_index:end_index]
            
            # Display the table.
            table = tabulate(
                records_per_page,
                headers=df.columns,
                tablefmt="grid",
                showindex=False,
            )
            print(table)

            # Check if we've reached the end of the records.
            if end_index >= total_records:
                print("\nEnd of records.")
                break

            # Ask the user for input to navigate pages.
            user_input = input("Press Enter to see more or 'q' to quit: ").strip().lower()
            if user_input == 'q':
                break
            
            # Update start index for the next page.
            start_index = end_index 

    def run(self):
        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name,
            "execution_uuid": self.args.execution_uuid
        }
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
                
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):  
            raise FileNotFound(mlmd_file_name, current_directory)

        # Creating cmfquery object.
        query = cmfquery.CmfQuery(mlmd_file_name)

        pipeline_name = self.args.pipeline_name[0]
        df = query.get_all_executions_in_pipeline(pipeline_name)

        # Check if the DataFrame is empty, indicating the pipeline name does not exist.
        if df.empty:    
            raise PipelineNotFound(pipeline_name)
        else:
            # Process execution ID if provided
            if not self.args.execution_uuid:         # If self.args.execution_uuid is None or an empty list ([]).
                pass
            else:
                df = df[df['Execution_uuid'].apply(lambda x: self.args.execution_uuid[0] in x.split(","))] # Used dataframe based on execution uuid
                if not df.empty:
                    # Rearranging columns: Start with fixed columns and appending the remaining columns.
                    updated_columns = ["id", "Context_Type", "Execution", "Execution_uuid", "name", "Pipeline_Type", "Git_Repo"] 
                    updated_columns += [ col for col in df.columns if col not in updated_columns]
                    
                    df = df[updated_columns]

                    # Drop columns that start with 'custom_properties_' and that contains NaN values
                    columns_to_drop = [col for col in df.columns if col.startswith('custom_properties_') and df[col].isna().any()]
                    df = df.drop(columns=columns_to_drop)

                    # Wrap text in object-type columns to a width of 30 characters.
                    for col in df.select_dtypes(include=['object']).columns:
                        df[col] = df[col].apply(lambda x: textwrap.fill(x, width=30) if isinstance(x, str) else x)
                    
                    # Set 'id' as the DataFrame index and transpose it for display horizontally.
                    df.set_index("id", inplace=True)
                    df = df.T.reset_index()
                    df.columns.values[0] = 'id'  # Rename the first column back to 'id'.

                    # Display the updated DataFrame as a formatted table.
                    table = tabulate(
                        df,
                        headers=df.columns,
                        tablefmt="grid",
                        showindex=False,
                    )
                    print(table)
                    print()
                    return MsgSuccess(msg_str = "Done.")
                return ExecutionUUIDNotFound(self.args.execution_uuid[0])
    
            self.display_table(df)             
            return MsgSuccess(msg_str = "Done.")
    
    
def add_parser(subparsers, parent_parser):
    EXECUTION_LIST_HELP = "Displays executions from the MLMD file with a few properties in a 7-column table, limited to 20 records per page."

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Displays executions from the MLMD file with a few properties in a 7-column table, limited to 20 records per page.",
        help=EXECUTION_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name",
        action="append", 
        required=True,
        help="Specify pipeline name.", 
        metavar="<pipeline_name>", 
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify the absolute or relative path for the input MLMD file.",
        metavar="<file_name>",
    )

    parser.add_argument(
        "-e", 
        "--execution_uuid", 
        action="append",
        help="Specify the execution uuid to retrieve execution.",
        metavar="<exe_uuid>",
    )

    parser.set_defaults(func=CmdExecutionList)
