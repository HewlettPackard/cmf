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

/**
 * Custom hook to manage data fetching operations for artifacts
 */
const useArtifactsData = (client, state) => {
  const {
    selectedPipeline,
    setSelectedPipeline,
    setPipelines,
    setArtifacts,
    artifactTypes,
    setArtifactTypes,
    selectedArtifactType,
    setSelectedArtifactType,
    sortOrder,
    activePage,
    filter,
    selectedCol,
    setTotalItems,
    setLoading,
    isLoadingLabelContent,
    pipelines
  } = state;

  // Fetch pipelines on component mount
  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      const defaultPipeline = data && data.length > 0 ? data[0] : null;
      setSelectedPipeline(defaultPipeline);
      if (!data || data.length === 0) {
        setLoading(false);
      }
    }).catch((error) => {
      console.error('Failed to fetch pipelines:', error);
      setPipelines([]);
      setSelectedPipeline(null);
      setLoading(false);
    });
  };

  const fetchArtifactTypes = () => {
    client.getArtifactTypes().then((types) => {
      setArtifactTypes(types);
      const defaultArtifactType = types && types.length > 0 ? types[0] : null;
      setSelectedArtifactType(defaultArtifactType);

      if (defaultArtifactType && selectedPipeline) {
        fetchArtifacts(selectedPipeline, defaultArtifactType, sortOrder, activePage, filter, selectedCol);
      } else {
        setLoading(false);
      }
    }).catch((error) => {
      console.error('Failed to fetch artifact types:', error);
      setArtifactTypes([]);
      setSelectedArtifactType(null);
      setLoading(false);
    });
  };

  const fetchArtifacts = async (pipelineName, artifactType, sortOrder, activePage, filter="", selectedCol) => {
    try {
      if (isLoadingLabelContent) {
        return;
      }

      setLoading(true);
      setArtifacts(null);

      // Handle Label search case
      if (artifactType === "Label" && filter && filter.trim() !== "") {
        try {
          const searchData = await client.searchLabelArtifacts(pipelineName, filter, sortOrder, activePage, 5);

          searchData.items.forEach(item => {
            item.isSearchResult = true;
            item.searchFilter = filter;
          });

          setArtifacts(searchData.items);
          setTotalItems(searchData.total_items);
          setLoading(false);
          return;
        } catch (searchError) {
          console.warn('Label search failed, falling back to regular fetch:', searchError);
        }
      }

      // Regular artifact fetching
      const regularData = await client.getArtifacts(pipelineName, artifactType, sortOrder, activePage, filter, selectedCol);
      setArtifacts(regularData.items);
      setTotalItems(regularData.total_items);

    } catch (error) {
      console.error('Failed to fetch artifacts:', error);
      setArtifacts([]);
      setTotalItems(0);
    } finally {
      setLoading(false);
    }
  };

  // Effects for data fetching
  useEffect(() => {
    fetchPipelines();
  }, []);

  useEffect(() => {
    if (selectedPipeline) {
      fetchArtifactTypes(selectedPipeline);
    } else if (selectedPipeline === null && pipelines.length === 0) {
      setLoading(false);
    }
  }, [selectedPipeline, pipelines.length]);

  useEffect(() => {
    if (selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType, sortOrder, activePage, filter, selectedCol);
    }
  }, [selectedPipeline, selectedArtifactType, sortOrder, activePage, selectedCol, filter]);

  return {
    fetchPipelines,
    fetchArtifactTypes,
    fetchArtifacts
  };
};

export default useArtifactsData;
