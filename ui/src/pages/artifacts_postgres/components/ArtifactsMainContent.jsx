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
import LabelContentPanel from "./LabelContentPanel";
import ResizableSplitPane from "./ResizableSplitPane";
import PaginationControls from "./PaginationControls";
import ArtifactsLeftPanel from "./ArtifactsLeftPanel";


const ArtifactsMainContent = ({
  selectedArtifactType,
  loading,
  artifacts,
  toggleSortOrder,
  toggleSortTime,
  filter,
  expandedRow,
  setExpandedRow,
  onLabelClick,
  // Label-specific props
  selectedTableLabel,
  labelContentLoading,
  labelData,
  parsedLabelData,
  labelColumns,
  currentPage,
  rowsPerPage,
  setCurrentPage,
  setRowsPerPage,
  // Pagination props
  totalItems,
  activePage,
  clickedButton,
  onPageClick,
  onPrevClick,
  onNextClick
}) => {
  if (selectedArtifactType === "Label") {
    return (
      <div className="flex-grow" style={{ height: 'calc(100vh - 200px)' }}>
        <ResizableSplitPane
          leftContent={
            <ArtifactsLeftPanel
              loading={loading}
              artifacts={artifacts}
              selectedArtifactType={selectedArtifactType}
              toggleSortOrder={toggleSortOrder}
              toggleSortTime={toggleSortTime}
              filter={filter}
              onLabelClick={onLabelClick}
              expandedRow={expandedRow}
              setExpandedRow={setExpandedRow}
            />
          }
          rightContent={
            <LabelContentPanel
              selectedTableLabel={selectedTableLabel}
              labelContentLoading={labelContentLoading}
              labelData={labelData}
              parsedLabelData={parsedLabelData}
              labelColumns={labelColumns}
              currentPage={currentPage}
              rowsPerPage={rowsPerPage}
              setCurrentPage={setCurrentPage}
              setRowsPerPage={setRowsPerPage}
            />
          }
          initialSplitPercentage={50}
        />
      </div>
    );
  }

  // Non-Label artifact types
  return (
    <div>
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader />
        </div>
      ) : artifacts !== null && artifacts.length > 0 ? (
        <ArtifactPTable
          artifacts={artifacts}
          artifactType={selectedArtifactType}
          onsortOrder={toggleSortOrder}
          onsortTimeOrder={toggleSortTime}
          filterValue={filter}
          expandedRow={expandedRow}
          setExpandedRow={setExpandedRow}
        />
      ) : (
        <div>No data available</div>
      )}
      {!loading && (
        <PaginationControls
          totalItems={totalItems}
          activePage={activePage}
          clickedButton={clickedButton}
          onPageClick={onPageClick}
          onPrevClick={onPrevClick}
          onNextClick={onNextClick}
        />
      )}
    </div>
  );
};

export default ArtifactsMainContent;
