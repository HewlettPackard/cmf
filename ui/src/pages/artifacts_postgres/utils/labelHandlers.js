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

// Helper function to evaluate a single search condition against a row
const evaluateSearchCondition = (row, condition) => {
  const columnValue = row[condition.column];

  if (columnValue === undefined || columnValue === null) {
    return false;
  }

  const columnStr = String(columnValue).trim();

  try {
    switch (condition.operator) {
      case "~": // Contains
        return columnStr.toLowerCase().includes(String(condition.value).toLowerCase());

      case "!~": // Not contains
        return !columnStr.toLowerCase().includes(String(condition.value).toLowerCase());

      case "=": // Equal
        return compareValues(columnStr, condition.value, "==");

      case "!=": // Not equal
        return compareValues(columnStr, condition.value, "!=");

      case ">": // Greater than
        return compareValues(columnStr, condition.value, ">");

      case "<": // Less than
        return compareValues(columnStr, condition.value, "<");

      case ">=": // Greater than or equal
        return compareValues(columnStr, condition.value, ">=");

      case "<=": // Less than or equal
        return compareValues(columnStr, condition.value, "<=");

      default:
        return false;
    }
  } catch (error) {
    console.warn("Error evaluating condition:", condition, error);
    return false;
  }
};

// Helper function to compare values with type coercion
const compareValues = (columnValue, conditionValue, operator) => {
  // If condition value is numeric, try to parse column value as numeric
  if (typeof conditionValue === "number") {
    try {
      const columnNumeric = parseFloat(columnValue);
      if (!isNaN(columnNumeric)) {
        switch (operator) {
          case "==": return columnNumeric === conditionValue;
          case "!=": return columnNumeric !== conditionValue;
          case ">": return columnNumeric > conditionValue;
          case "<": return columnNumeric < conditionValue;
          case ">=": return columnNumeric >= conditionValue;
          case "<=": return columnNumeric <= conditionValue;
        }
      }
    } catch (error) {
      // Fall back to string comparison
    }
  }

  // String comparison
  const columnStr = columnValue.toLowerCase();
  const conditionStr = String(conditionValue).toLowerCase();

  switch (operator) {
    case "==": return columnStr === conditionStr;
    case "!=": return columnStr !== conditionStr;
    case ">": return columnStr > conditionStr;
    case "<": return columnStr < conditionStr;
    case ">=": return columnStr >= conditionStr;
    case "<=": return columnStr <= conditionStr;
    default: return false;
  }
};

// Handle label click from table
export const handleTableLabelClick = async (
  labelName,
  artifact,
  client,
  setters,
  context = {}
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

  // Extract search filter and pipeline name from context and artifact
  const searchFilter = context.searchFilter || (artifact.search_metadata?.search_term);
  const pipelineName = context.pipelineName;

  console.log('Loading label data with search filter:', searchFilter, 'for artifact:', artifact.name);

  try {
    // Clear old data first
    setParsedLabelData([]);
    setLabelColumns([]);

    // Helper function to try different URI formats
    const tryGetLabelData = async (labelName, fileNameForAPI, searchFilter, pipelineName) => {
      const uriFormatsToTry = [
        fileNameForAPI,                           // Original: artifacts/labels.csv:93951bf...
        labelName,                                // Just the label name: 93951bf...
        `artifacts/labels.csv/${labelName}`,      // Alternative format: artifacts/labels.csv/93951bf...
        `labels.csv:${labelName}`,                // Without artifacts prefix: labels.csv:93951bf...
        `${labelName}.csv`                        // As CSV file: 93951bf....csv
      ];

      for (const uriToTry of uriFormatsToTry) {
        try {
          // For label click scenario, use fallback_to_full=true so that if search filter doesn't match any rows,
          // we still get the full CSV content instead of empty results
          const data = await client.getLabelData(uriToTry, searchFilter, pipelineName, true);
          return data; // Success - return immediately
        } catch (uriError) {
          continue; // Try next URI format
        }
      }

      throw new Error(`All URI formats failed. Tried: ${uriFormatsToTry.join(', ')}`);
    };

    const labelData = await tryGetLabelData(labelName, fileNameForAPI, searchFilter, pipelineName);

    setLabelData(labelData);

    const parsed = Papa.parse(labelData, { header: true });

    // Check if we passed a search filter to the backend API
    // If we did, the backend has already filtered the data, so we should NOT apply additional filtering
    if (searchFilter) {
      console.log('Backend already filtered data with search filter:', searchFilter, 'showing', parsed.data.length, 'rows');
      // Backend has already applied the search filter, so just display the returned data
      setParsedLabelData(parsed.data);
    } else if (artifact.isSearchResult && artifact.searchFilter &&
        (artifact.search_metadata?.content_match || artifact.search_metadata?.advanced_conditions)) {
      // This is a search result but we didn't pass the search filter to backend
      // Apply frontend filtering (this is the old behavior for backward compatibility)
      const searchFilter = artifact.searchFilter;
      const searchMetadata = artifact.search_metadata;

      console.log('Processing search result for label:', labelName, 'with', parsed.data.length, 'total rows');

      // Apply advanced search filtering if conditions are present
      if (searchMetadata.advanced_conditions && searchMetadata.advanced_conditions.length > 0) {
        console.log('Applying advanced search conditions:', searchMetadata.advanced_conditions);
        // Apply advanced search conditions
        const matchingRows = parsed.data.filter((row) => {
          // Check if row matches all advanced conditions
          const conditionsMatch = searchMetadata.advanced_conditions.every(condition => {
            return evaluateSearchCondition(row, condition);
          });

          // Check if row matches plain text terms (if any)
          let plainTermsMatch = true;
          if (searchMetadata.plain_terms && searchMetadata.plain_terms.length > 0) {
            const rowValues = Object.values(row);
            plainTermsMatch = searchMetadata.plain_terms.every(term => {
              return rowValues.some(value => {
                return value && value.toString().toLowerCase().includes(term.toLowerCase());
              });
            });
          }

          return conditionsMatch && plainTermsMatch;
        });

        console.log('Advanced search filtering result:', matchingRows.length, 'of', parsed.data.length, 'rows matched');

        setParsedLabelData(matchingRows);
      } else {
        // Fall back to basic text search
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
      }
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
