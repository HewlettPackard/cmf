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

import { useEffect } from "react";
import { handleTableLabelClick, clearLabelData } from "../utils/labelHandlers";

/**
 * Custom hook to manage event handlers for the artifacts page
 */
const useArtifactsHandlers = (client, state) => {
  const {
    selectedArtifactType,
    setSelectedArtifactType,
    setActivePage,
    setLoading,
    setArtifacts,
    setSelectedTableLabel,
    setLabelData,
    setParsedLabelData,
    setLabelColumns,
    setLabelContentLoading,
    setCurrentPage,
    selectedPipeline,
    setSelectedPipeline,
    setFilter,
    setSortOrder,
    setSelectedCol,
    setClickedButton,
    activePage,
    totalItems,
    filter,
    expandedRow,
    setExpandedRow,
    setIsLoadingLabelContent
  } = state;

  // Reset accordion state when artifact type changes
  useEffect(() => {
    setExpandedRow(null);
  }, [selectedArtifactType]);

  // Handle accordion auto-expansion for search filters
  useEffect(() => {
    if (selectedArtifactType === "Label") {
      if (filter && filter.trim() !== "") {
        setExpandedRow("all");
      }
    }
  }, [filter, selectedArtifactType]);

  const handleArtifactTypeClick = (artifactType) => {
    if (selectedArtifactType !== artifactType) {
      setLoading(true);
      setArtifacts(null);
    }
    setSelectedArtifactType(artifactType);
    setActivePage(1);

    // Clear label-related state when switching artifact types
    setSelectedTableLabel(null);
    clearLabelData({
      setLabelData,
      setParsedLabelData,
      setLabelColumns,
      setLabelContentLoading,
      setCurrentPage
    });
  };

  const handlePipelineClick = (pipeline) => {
    if (selectedPipeline !== pipeline) {
      setLoading(true);
      setArtifacts(null);
    }
    setSelectedPipeline(pipeline);
    setActivePage(1);

    // Clear label-related state when switching pipelines
    setSelectedTableLabel(null);
    clearLabelData({
      setLabelData,
      setParsedLabelData,
      setLabelColumns,
      setLabelContentLoading,
      setCurrentPage
    });
  };

  const handleFilter = (value) => {
    setFilter(value);
    setActivePage(1);
  };

  const toggleSortOrder = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("name");
  };

  const toggleSortTime = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("create_time_since_epoch");
  };

  const handlePageClick = (page) => {
    setActivePage(page);
    setClickedButton("page");
  };

  const handlePrevClick = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
      setClickedButton("prev");
      handlePageClick(activePage - 1);
    }
  };

  const handleNextClick = () => {
    if (activePage < Math.ceil(totalItems / 5)) {
      setActivePage(activePage + 1);
      setClickedButton("next");
      handlePageClick(activePage + 1);
    }
  };

  // Handle label click from table
  const handleLabelClick = async (labelName, artifact) => {
    await handleTableLabelClick(labelName, artifact, client, {
      setIsLoadingLabelContent,
      setSelectedTableLabel,
      setLabelContentLoading,
      setCurrentPage,
      setParsedLabelData,
      setLabelColumns,
      setLabelData
    }, {
      searchFilter: filter,
      pipelineName: selectedPipeline
    });
  };

  return {
    handleArtifactTypeClick,
    handlePipelineClick,
    handleFilter,
    toggleSortOrder,
    toggleSortTime,
    handlePageClick,
    handlePrevClick,
    handleNextClick,
    handleLabelClick
  };
};

export default useArtifactsHandlers;
