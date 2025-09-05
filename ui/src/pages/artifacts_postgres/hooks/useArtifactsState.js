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

import { useState } from "react";

/**
 * Custom hook to manage all state variables for the artifacts page
 */
const useArtifactsState = () => {
  // Pipeline and artifact state
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [artifactTypes, setArtifactTypes] = useState([]);
  const [selectedArtifactType, setSelectedArtifactType] = useState(null);
  
  // Filter and sorting state
  const [filter, setFilter] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [selectedCol, setSelectedCol] = useState("name");
  
  // Pagination state
  const [totalItems, setTotalItems] = useState(0);
  const [activePage, setActivePage] = useState(1);
  const [clickedButton, setClickedButton] = useState("page");
  
  // Loading state
  const [loading, setLoading] = useState(true);
  
  // Label-specific state
  const [selectedTableLabel, setSelectedTableLabel] = useState(null);
  const [labelData, setLabelData] = useState("");
  const [parsedLabelData, setParsedLabelData] = useState([]);
  const [labelColumns, setLabelColumns] = useState([]);
  const [labelContentLoading, setLabelContentLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Flag to prevent re-fetching artifacts when just loading label content
  const [isLoadingLabelContent, setIsLoadingLabelContent] = useState(false);
  
  // Accordion state
  const [expandedRow, setExpandedRow] = useState(null);

  return {
    // Pipeline and artifact state
    selectedPipeline,
    setSelectedPipeline,
    pipelines,
    setPipelines,
    artifacts,
    setArtifacts,
    artifactTypes,
    setArtifactTypes,
    selectedArtifactType,
    setSelectedArtifactType,
    
    // Filter and sorting state
    filter,
    setFilter,
    sortOrder,
    setSortOrder,
    selectedCol,
    setSelectedCol,
    
    // Pagination state
    totalItems,
    setTotalItems,
    activePage,
    setActivePage,
    clickedButton,
    setClickedButton,
    
    // Loading state
    loading,
    setLoading,
    
    // Label-specific state
    selectedTableLabel,
    setSelectedTableLabel,
    labelData,
    setLabelData,
    parsedLabelData,
    setParsedLabelData,
    labelColumns,
    setLabelColumns,
    labelContentLoading,
    setLabelContentLoading,
    currentPage,
    setCurrentPage,
    rowsPerPage,
    setRowsPerPage,
    
    // Flags
    isLoadingLabelContent,
    setIsLoadingLabelContent,
    
    // Accordion state
    expandedRow,
    setExpandedRow
  };
};

export default useArtifactsState;
