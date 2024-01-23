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
import Footer from "../../components/Footer";
import LineageSidebar from "../../components/LineageSidebar";
import LineageTypeSidebar from "./LineageTypeSidebar";
import LineageArtifacts from "../../components/LineageArtifacts";
const client = new FastAPIClient(config);

const Lineage = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);

//  const LineageTypes=['Artifacts','Execution','ArtifactExecution']
  const LineageTypes=['Artifacts']
  const [selectedLineageType, setSelectedLineageType] = useState(null);

  const [lineageArtifactsKey, setLineageArtifactsKey] = useState(0);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };

  useEffect(() => {
    fetchPipelines();
  }, []);

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline);
  };

  const handleLineageTypeClick = (lineageType) => {
    setSelectedLineageType(lineageType);
  };  

  const fetchLineageTypes = () => {
      handleLineageTypeClick(LineageTypes[0]);
  };

  useEffect(() => {
    if (selectedPipeline) {
      fetchLineageTypes(selectedPipeline);
    }
    // eslint-disable-next-line 
 }, [selectedPipeline]);

  const fetchLineage = (pipelineName, type) => {
    client.getLineage(pipelineName,type).then((data) => {
    });
  };

  useEffect(() => {
    if (selectedPipeline && selectedLineageType) {
      fetchLineage(selectedPipeline, selectedLineageType);
      setLineageArtifactsKey((prevKey) => prevKey + 1);
    }
  }, [selectedPipeline, selectedLineageType]);

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />

        <div className="container">
          <div className="flex flex-row">
            <LineageSidebar
              pipelines={pipelines}
              handlePipelineClick={handlePipelineClick}
            />
          <div className="container justify-center items-center mx-auto px-4">
            <div className="flex flex-col">
             {selectedPipeline !== null && (
                <LineageTypeSidebar
                  LineageTypes={LineageTypes}
                  handleLineageTypeClick= {handleLineageTypeClick}
                />
             )}
            </div>
            <div className="container">
                {selectedPipeline !== null && (
                <LineageArtifacts key={lineageArtifactsKey} />
              )}
            </div>
          </div>
        </div>
       </div>
        <Footer />
      </section>
    </>
  );
};

export default Lineage;
