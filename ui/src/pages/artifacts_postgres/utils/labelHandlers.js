/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

import Papa from "papaparse";

// Handle label click from table
export const handleTableLabelClick = async (
  labelName, 
  artifact, 
  client,
  setters
) => {
  const {
    setIsLoadingLabelContent,
    setSelectedTableLabel,
    setLabelContentLoading,
    setCurrentPage,
    setParsedLabelData,
    setLabelColumns,
    setLabelData
  } = setters;

  // Set loading flag to prevent fetchArtifacts from running
  setIsLoadingLabelContent(true);

  // Batch state updates to minimize re-renders
  setSelectedTableLabel(artifact);
  setLabelContentLoading(true);
  setCurrentPage(0); // Reset pagination when new label is selected

  // Use the URI from the artifact for getLabelData, not just the label name
  const fileNameForAPI = artifact.uri || `artifacts/labels.csv:${labelName}`;

  try {
    // Clear old data first
    setParsedLabelData([]);
    setLabelColumns([]);

    // Helper function to try different URI formats
    const tryGetLabelData = async (labelName, fileNameForAPI) => {
      const uriFormatsToTry = [
        fileNameForAPI,                           // Original: artifacts/labels.csv:93951bf...
        labelName,                                // Just the label name: 93951bf...
        `artifacts/labels.csv/${labelName}`,      // Alternative format: artifacts/labels.csv/93951bf...
        `labels.csv:${labelName}`,                // Without artifacts prefix: labels.csv:93951bf...
        `${labelName}.csv`                        // As CSV file: 93951bf....csv
      ];

      for (const uriToTry of uriFormatsToTry) {
        try {
          const data = await client.getLabelData(uriToTry);
          return data; // Success - return immediately
        } catch (uriError) {
          continue; // Try next URI format
        }
      }

      throw new Error(`All URI formats failed. Tried: ${uriFormatsToTry.join(', ')}`);
    };

    const labelData = await tryGetLabelData(labelName, fileNameForAPI);

    setLabelData(labelData);

    const parsed = Papa.parse(labelData, { header: true });

    // Check if this is a search result and if the search term was found in CSV content
    if (artifact.isSearchResult && artifact.searchFilter && artifact.search_metadata?.content_match) {
      const searchFilter = artifact.searchFilter;

      // Filter CSV rows to show only those containing the search term
      const matchingRows = parsed.data.filter((row) => {
        const rowValues = Object.values(row);

        const hasMatch = rowValues.some(value => {
          if (value && value.toString().toLowerCase().includes(searchFilter.toLowerCase())) {
            return true;
          }
          return false;
        });

        return hasMatch;
      });

      setParsedLabelData(matchingRows);
    } else {
      // Normal label OR search result with property-only match - show all data
      setParsedLabelData(parsed.data);
    }

    if (parsed.meta.fields) {
      setLabelColumns(
        parsed.meta.fields.map(field => ({
          name: field,
          selector: row => row[field],
          sortable: true,
        }))
      );
    }
  } catch (error) {
    // Clear data on error to prevent showing old content
    setParsedLabelData([]);
    setLabelColumns([]);

    // Show error message to user
    setParsedLabelData([{
      error: "Failed to load label content",
      message: error.message,
      uri: fileNameForAPI
    }]);

  } finally {
    setLabelContentLoading(false);
    setIsLoadingLabelContent(false); // Reset flag to allow normal useEffect behavior
  }
};

// Clear label data utility
export const clearLabelData = (setters) => {
  const {
    setLabelData,
    setParsedLabelData,
    setLabelColumns,
    setLabelContentLoading,
    setCurrentPage
  } = setters;

  setLabelData("");
  setParsedLabelData([]);
  setLabelColumns([]);
  setLabelContentLoading(false);
  setCurrentPage(0);
};
