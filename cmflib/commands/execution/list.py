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

from cmflib.cli.command import CmdBase
from cmflib import cmfquery
from tabulate import tabulate
from cmflib.dvc_wrapper import dvc_get_config

class CmdExecutionList(CmdBase):

    def update_dataframe(self, df, is_long):
        """
        Updates the dataframe to fit the specified table format based on the length option.

        Parameters:
        - df: DataFrame to be updated.
        - is_long: Boolean indicating whether to use long option or not.

        Returns:
        - Updated DataFrame with selected columns.
        """
        if is_long:
            updated_columns = ["id", "Context_Type"] + [ col for col in df.columns if not (col == "id" or col == "Context_Type")]
        else:
            updated_columns = ["id", "Context_Type"] + [ col for col in df.columns if col.startswith('custom_properties_')]
            # Limit to a maximum of 5 columns.
            if len(updated_columns) > 5:
                updated_columns = updated_columns[:5]

        return df[updated_columns]
    
    
    def display_table(self, df, char_size, is_custom_prop):
        """
        Displays the dataframe in a table format, optionally renaming columns and wrapping text.

        Parameters:
        - df: DataFrame to display.
        - char_size: Character width for text wrapping.
        - is_custom_prop: Boolean indicating if custom properties named column are used or not.
        """
        if is_custom_prop:
            # Rename columns.
            df = df.rename(columns = lambda x: x.replace("custom_properties_", "") if x.startswith("custom_properties_") else x)
        
        # Wrapping text in object columns.
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=char_size) if isinstance(x, str) else x)

        total_records = len(df)
        start_index = 0  

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
        # Check if 'cmf' is configured
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        elif len(self.args.file_name) > 1:  # If the user provided more than one file name. 
            return "Error: You can only provide one file name using the -f flag."
        elif not self.args.file_name[0]:    # self.args.file_name[0] is an empty string (""). 
            return "Error: Missing File name"
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):  
            return f"Error: {mlmd_file_name} doesn't exists in {current_directory} directory."

        # Creating cmfquery object.
        query = cmfquery.CmfQuery(mlmd_file_name)

        # Check if pipeline exists in mlmd.
        if self.args.pipeline_name is not None and len(self.args.pipeline_name) > 1:  
            return "Error: You can only provide one pipeline name using the -p flag."
        elif not self.args.pipeline_name[0]:    # self.args.pipeline_name[0] is an empty string ("").   
            return "Error: Missing pipeline name"
        else:
            pipeline_name = self.args.pipeline_name[0]
        
        df = query.get_all_executions_in_pipeline(pipeline_name)

        # Check if the DataFrame is empty, indicating the pipeline name does not exist.
        if df.empty:    
            return "Pipeline does not exist.."
        else:
            # Drop the 'Python_Env' column if it exists in the DataFrame.
            if "Python_Env" in df.columns:
                df = df.drop(['Python_Env'], axis=1)  # Type of df is series of integers.

            # Process execution ID if provided
            if not self.args.execution_id:         # If self.args.execution_id is None or an empty list ([]).
                pass
            elif len(self.args.execution_id) > 1:  # If the user provided more than one execution_id.  
                return "Error: You can only provide one execution id using the -e flag."
            elif not self.args.execution_id[0]:    # self.args.execution_id[0] is an empty string ("").
                return "Error: Missing execution id"
            else:
                if self.args.execution_id[0].isdigit():
                    if int(self.args.execution_id[0]) in list(df['id']): # Converting series to list.
                        df = df.query(f'id == {int(self.args.execution_id[0])}')
                        df = self.update_dataframe(df, True)

                        # Wrap text in object columns to fit within 30 characters.
                        for col in df.select_dtypes(include=['object']).columns:
                            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=30) if isinstance(x, str) else x)
                        
                        # Set 'id' as the DataFrame index and transpose it for display horizontally.
                        df.set_index("id", inplace=True)
                        df = df.T.reset_index()
                        df.columns.values[0] = 'id'  # Rename the first column back to 'id'.

                        # Display the filtered DataFrame as a formatted table.
                        table = tabulate(
                            df,
                            headers=df.columns,
                            tablefmt="grid",
                            showindex=False,
                        )
                        print(table)
                        print()
                        return "Done"
                return "Execution id does not exist.."  

            # Update and display the full DataFrame based on the long option.    
            if self.args.long:
                df = self.update_dataframe(df, True)

                # Limit to a maximum of 7 columns.
                if len(df.columns) > 7:
                    df=df.iloc[:,:7]
                self.display_table(df, 15, True)
            else:
                df = self.update_dataframe(df, False)
                self.display_table(df, 25, True) 
                
            return "Done"
    
    
def add_parser(subparsers, parent_parser):
    EXECUTION_LIST_HELP = '''Display all executions with detailed information from the specified MLMD file. 
                             By default, records are displayed in table format with 5 columns and a limit of 20 records per page.'''

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display all executions with detailed information from the specified MLMD file.",
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
        "--execution_id", 
        action="append",
        help="Specify the execution id to retrieve execution.",
        metavar="<exe_id>",
    )
    
    parser.add_argument(
        "-l",
        "--long", 
        action='store_true',
        help="Use to display 20 records per page in a table with 7 columns.",
    )

    parser.set_defaults(func=CmdExecutionList)