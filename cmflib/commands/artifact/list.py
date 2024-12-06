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
from typing import Union, List

class CmdArtifactsList(CmdBase):
    def update_dataframe(self, df: pd.DataFrame, is_long: bool) -> pd.DataFrame:
        """
        Reorders and updates the DataFrame columns.

        Parameters:
        - df: The input DataFrame to be updated.
        - is_long: 
            - If True, includes all columns after prioritizing 'id', 'name', and 'date_time' columns.
            - If False, includes only columns starting with 'custom_properties' after prioritizing 'id', 'name', and 'date_time' columns.

        Returns:
        - pd.DataFrame: A new DataFrame with reordered columns.
        """

        # Convert the 'create_time_since_epoch' column to UTC datetime format.
        # The datetime is formatted as "Day DD Mon YYYY HH:MM:SS GMT".
        df = df.copy()
        df['date_time'] = pd.to_datetime(df['create_time_since_epoch'], unit='ms', utc=True).dt.strftime("%a %d %b %Y %H:%M:%S GMT")
        df.drop('create_time_since_epoch', axis=1, inplace=True) # Removing column from dataframe.

        if is_long:
            # When user specify -l option(i.e long) in that case we need to print id, name and date_time as a 1st 3 columns in table
            # and after that all the remaining columns.
            updated_columns = ["id", "name", "date_time"] + [ col for col in df.columns if not (col == "id" or col == "name" or col == "date_time")]
        else:
            # In case of short option(that is default option) we need to print id, name and date_time as a 1st 3 columns in table
            # and after that need to print all columns which is start with "custom_properties".
            updated_columns = ["id", "name", "date_time"] + [ col for col in df.columns if col.startswith('custom_properties_')]

        return df[updated_columns]
    
    def display_table(self, df: pd.DataFrame) -> None:
        """
        Displays the DataFrame in a paginated table format with optional column renaming and text wrapping for better readability. 
        Parameters: 
        - df: The DataFrame to display.
        """
        # Limit the table to a maximum of 8 columns to ensure proper formatting and readability.
        # Tables with more than 8 columns may appear cluttered or misaligned on smaller terminal screens. 
        if len(df.columns) > 8:
            df=df.iloc[:,:8]

        # Rename columns that start with "custom_properties_" by removing the prefix for clarity. 
        # For example, "custom_properties_auc_curve" becomes "auc_curve". 
        df = df.rename(columns = lambda x: x.replace("custom_properties_", "") if x.startswith("custom_properties_") else x)

        # Wrap text in object-type columns to a width of 15 characters.
        # This ensures that long strings are displayed neatly within the table.
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(lambda x: textwrap.fill(x, width=15) if isinstance(x, str) else x)

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

    def search_artifact(self, df: pd.DataFrame) -> Union[int, List[int]]:
        """
        Searches for the specified 'artifact_name' in the DataFrame and returns matching IDs.

        Parameters:
        - df: DataFrame to search within.

        Returns:
        - List of matching IDs or -1 if no matches are found.
        """
        # Example of a given sample 'artifact_name' --> artifacts/parsed/train.tsv:12345
        # These are the combinations we are implementing:
        # 1. artifacts/parsed/train.tsv
        # 2. train.tsv   
        # 3. artifacts/parsed/train.tsv:12345
        # 4. train.tsv:12345
        
        # In case of multiple occurrences of 'artifact_name', we need to store the IDs of all matching names.
        # For example, if "metrics" appears multiple times, we store all its IDs.
        matched_ids = []
        artifact_name = self.args.artifact_name[0].strip()
        for index, row in df.iterrows():
            # Extract the base name from the row.
            # eg. artifacts/parsed/train.tsv:12345 --> artifacts/parsed/train.tsv
            name =  row['name'].split(":")[0]      
            if artifact_name == name:             # Match the full path: artifacts/parsed/train.tsv
                matched_ids.append(row['id'])     
            elif artifact_name == name.split('/')[-1]:    # Match only the file name: train.tsv
                matched_ids.append(row['id'])
            elif artifact_name == row['name']:             # Match the full path with hash: artifacts/parsed/train.tsv:12345
                matched_ids.append(row['id'])
            elif artifact_name == row["name"].split('/')[-1]:   # Match only the file name with hash: train.tsv:12345
                matched_ids.append(row['id'])
        
        if len(matched_ids) != 0:
            return matched_ids
        return -1

    def run(self):
        # Check if 'cmf' is configured.
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
        
        df = query.get_all_artifacts_by_context(pipeline_name)

        if df.empty:
            return "Pipeline name doesn't exists..."
        else:
            if not self.args.artifact_name:         # If self.args.artifact_name is None or an empty list ([]). 
                pass
            elif len(self.args.artifact_name) > 1:  # If the user provided more than one artifact_name. 
                 return "Error: You can only provide one artifact name using the -a flag."
            elif not self.args.artifact_name[0]:    # self.args.artifact_name[0] is an empty string ("").
                 return "Error: Missing artifact name"
            else:
                artifact_ids = self.search_artifact(df)
                if(artifact_ids != -1):
                    # Multiple/Single artifact names exist with the same name.
                    for artifact_id in artifact_ids:
                        # Filter the DataFrame to retrieve rows corresponding to the current ID.
                        filtered_data = df.loc[df['id'] == artifact_id] 
        
                        # Update the filtered data using the long format (include all columns).
                        filtered_data = self.update_dataframe(filtered_data, True)
                        
                        # Wrap text in object-type columns to a width of 30 characters for better readability.
                        for col in filtered_data.select_dtypes(include=['object']).columns:
                            filtered_data[col] = filtered_data[col].apply(lambda x: textwrap.fill(x, width=30) if isinstance(x, str) else x)

                        # For a single artifact name, display the table in a horizontal format:
                        # Set 'id' as the index.
                        filtered_data.set_index("id", inplace=True)
                        # Transpose the DataFrame to make rows into columns.
                        filtered_data = filtered_data.T.reset_index()
                        # Rename the first column back to 'id' for consistency.
                        filtered_data.columns.values[0] = 'id'

                        # Display the formatted and transposed table using the 'tabulate' library.
                        table = tabulate(
                            filtered_data,
                            headers=filtered_data.columns,  # Use column names as headers.
                            tablefmt="grid",                # Use grid format for table borders.
                            showindex=False,                # Do not display the default index.
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
        else:
            df = self.update_dataframe(df, False)
        self.display_table(df)

        return "Done."



def add_parser(subparsers, parent_parser):
    ARTIFACT_LIST_HELP = "Display all artifacts with detailed information from the specified MLMD file. By default, records are displayed in table format with 5 columns and a limit of 20 records per page."

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display all artifacts with detailed information from the specified MLMD file. By default, records are displayed in table format with 5 columns and a limit of 20 records per page.",
        help=ARTIFACT_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name", 
        required=True,
        action="append",
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
        "-a", 
        "--artifact_name", 
        action="append",
        help="Specify the artifact name to display detailed information about the given artifact name.",
        metavar="<artifact_name>",
    )

    parser.add_argument(
        "-l", 
        "--long", 
        action='store_true',
        help="Use to display 20 records per page in a table with 7 columns.",
    )

    parser.set_defaults(func=CmdArtifactsList)