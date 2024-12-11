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

import React, { useEffect, useState } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import ArtifactPsTable from "../../components/ArtifactPsTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";
import ArtifactPsTypeSidebar from "../../components/ArtifactPsTypeSidebar";

const client = new FastAPIClient(config);

const Artifacts_ps = () => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  // undefined state is to check whether artifacts data is set
  // null state of artifacts we display No Data
  const [artifacts, setArtifacts] = useState([]);
  const [artifactTypes, setArtifactTypes] = useState([]);
  const [selectedArtifactType, setSelectedArtifactType] = useState(null);
  const [filter, setFilter] = useState("");
  const [sortOrder_initial, setSortOrder] = useState("asc");
 

  // Fetch pipelines on component mount
  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      const defaultPipeline = data[0];
      setSelectedPipeline(defaultPipeline); // Set the first pipeline as default
      fetchArtifactTypes(defaultPipeline); // Fetch artifact types once the pipeline is selected
    });
  };

  const fetchArtifactTypes = (pipeline) => {
    client.getArtifactTypes().then((types) => {
      setArtifactTypes(types);
      const defaultArtifactType = types[0];
      setSelectedArtifactType(defaultArtifactType); // Set the first artifact type as default
      fetchArtifacts(pipeline, defaultArtifactType, filter, sortOrder_initial); // Fetch artifacts for the first artifact type and default pipeline
    });
  };

  const fetchArtifacts = (pipelineName, artifactType, filter="", sortOrder_initial) => {
    client.getArtifact(pipelineName, artifactType, filter, sortOrder_initial)
      .then((data) => {
        setArtifacts(data); // Update artifacts when data is fetched
      });
  };

  const handleArtifactTypeClick = (artifactType) => {
    setSelectedArtifactType(artifactType); // Set the selected artifact type
    setArtifacts(null); // Reset artifacts to null to indicate a new fetch
    if (selectedPipeline) {
      fetchArtifacts(selectedPipeline, artifactType, filter, sortOrder_initial); // Fetch artifacts based on the selected artifact type and pipeline
    }
  };

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline); // Set the selected pipeline
    setArtifacts(null); // Reset artifacts to null to indicate a new fetch
    fetchArtifacts(pipeline, selectedArtifactType, filter, sortOrder_initial); // Fetch artifacts based on the selected pipeline and artifact type
  };

  const handleFilter = (value) => {
    setFilter(value); // Update the filter string
    console.log("value",value)
  };

  useEffect(() => {
    fetchPipelines(); // Fetch pipelines and artifact types when the component mounts
  }, [filter, sortOrder_initial]);

  return (
    <>
      <section
        className="flex flex-col bg-white min-h-screen"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-grow" style={{ padding: "1px" }}>
          <div className="sidebar-container min-h-140 bg-gray-100 pt-2 pr-2 pb-4 w-1/6 flex-grow-0">
            <Sidebar
              pipelines={pipelines}
              handlePipelineClick={handlePipelineClick}
              className="flex-grow"
            />
          </div>
          <div className="w-5/6 justify-center items-center mx-auto px-4 flex-grow">
            <div className="flex flex-col w-full">
                {selectedPipeline !== null && (
                  <ArtifactPsTypeSidebar
                    artifactTypes={artifactTypes}
                    handleArtifactTypeClick={handleArtifactTypeClick}
                    onFilter={handleFilter}
                  />
                )}
            </div>
            <div>
                {artifacts !== null && artifacts.length > 0 ? (
                  <ArtifactPsTable 
                    artifacts={artifacts}
                    sortOrder_initial={sortOrder_initial}
                    />
                    
                ) : (
                  <div>No data available</div> // Display message when there are no artifacts
                )}
            </div>
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};
export default Artifacts_ps;
