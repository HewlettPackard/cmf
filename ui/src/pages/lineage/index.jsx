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
import Sidebar from "../../components/Sidebar";
import LineageTypeSidebar from "./LineageTypeSidebar";
import LineageArtifacts from "../../components/LineageArtifacts";
import ExecutionDropdown from "../../components/ExecutionDropdown";
const client = new FastAPIClient(config);

const Lineage = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);

  const LineageTypes=['Artifacts','Execution'];
  const [selectedLineageType, setSelectedLineageType] = useState('Artifacts');
  const [selectedExecutionType, setSelectedExecutionType] = useState(null);
  const [lineageData, setLineageData]=useState(null);
  const [executionData, setExecutionData]=useState(null);
  const [lineageArtifactsKey, setLineageArtifactsKey] = useState(0);
  const [execDropdownData,setExecDropdownData] = useState([]);

  // fetching list of pipelines
  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
      // when pipeline is updated we need to update the lineage selection too
      // in my opinion this is also not needed as we have selectedLineage has
      // default value
      if (data[0]) {
        setSelectedLineageType(LineageTypes[0]);
        // call artifact lineage as it is default
        fetchArtifactLineage(data[0], "Artifacts");
      }
    });
  };
  const handlePipelineClick = (pipeline) => {
    setLineageData(null);
    setSelectedPipeline(pipeline);
    // when pipeline is updated we need to update the lineage selection too
    // this is also not needed as selectedLineage has default value
    // setSelectedLineageType(LineageTypes[0]);
     if (selectedPipeline) {
       setSelectedLineageType(LineageTypes[0]);
       //call artifact lineage as it is default
       fetchArtifactLineage(selectedPipeline, selectedLineageType);
     }
  };

  const handleLineageTypeClick = (lineageType) => {
    setLineageData(null);
    setExecutionData(null);
    setSelectedLineageType(lineageType);
    if (lineageType === "Artifacts") {
      fetchArtifactLineage(selectedPipeline, lineageType);
    }
    else {
      fetchArtifactLineage(selectedPipeline, "Execution");
    }
  };  

  const fetchArtifactLineage = (pipelineName, type) => {
    client.getLineage(pipelineName,type).then((data) => {    
      if (type === "Artifacts") {
        setLineageData(data);
      } 
      else {
        setExecDropdownData(data);
        const typeParts = data[0].split('/');
        const exec_type = typeParts[1].split('_')[0];
        fetchExecutionLineage(pipelineName, exec_type);
      }
    });
    setLineageArtifactsKey((prevKey) => prevKey + 1);
  };

  // used for execution drop down
  const handleExecutionClick = (executionType) => {
    setExecutionData(null);
    const typeParts = executionType.split('/');
    const type = typeParts[1].split('_')[0];
    fetchExecutionLineage(selectedPipeline, type);
  };  

  const fetchExecutionLineage = (pipelineName, type) => {
    client.getExecutionLineage(pipelineName,type).then((data) => {    
      setExecutionData(data);
    });
  };

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />

        <div className="container">
          <div className="flex flex-row">
            <Sidebar
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
                {selectedPipeline !== null && selectedLineageType === "Artifacts" && lineageData !== null && (
                <LineageArtifacts key={lineageArtifactsKey} data={lineageData}/>
              )}
                {selectedPipeline !== null && selectedLineageType === "Execution" && execDropdownData !== null  && executionData !== null &&(
                <div>
                <ExecutionDropdown data={execDropdownData} handleExecutionClick= {handleExecutionClick}/>        
                <LineageArtifacts key={lineageArtifactsKey} data={executionData}/>
                </div>
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
