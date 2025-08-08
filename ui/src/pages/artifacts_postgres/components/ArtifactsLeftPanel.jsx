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

import React from "react";
import ArtifactPTable from "../../../components/ArtifactPTable";
import Loader from "../../../components/Loader";


const ArtifactsLeftPanel = ({
  loading,
  artifacts,
  selectedArtifactType,
  toggleSortOrder,
  toggleSortTime,
  filter,
  onLabelClick,
  expandedRow,
  setExpandedRow
}) => {
  return (
    <div className="p-4">
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader />
        </div>
      ) : artifacts !== null && artifacts?.length > 0 ? (
        <ArtifactPTable
          artifacts={artifacts}
          artifactType={selectedArtifactType}
          onsortOrder={toggleSortOrder}
          onsortTimeOrder={toggleSortTime}
          filterValue={filter}
          onLabelClick={selectedArtifactType === "Label" ? onLabelClick : undefined}
          expandedRow={expandedRow}
          setExpandedRow={setExpandedRow}
        />
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600">No label artifacts available</p>
        </div>
      )}
    </div>
  );
};

export default ArtifactsLeftPanel;
