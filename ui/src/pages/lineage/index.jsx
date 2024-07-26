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
import TangledTree from "../../components/TangledTree";
import ExecutionDropdown from "../../components/ExecutionDropdown";
import ExecutionTree from "../../components/ExecutionTree";
import ExecutionTangledDropdown from "../../components/ExecutionTangledDropdown";

const client = new FastAPIClient(config);

const Lineage = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const LineageTypes=['Artifacts','Execution','Tangled_Execution','Artifact_Tree'];
  const [selectedLineageType, setSelectedLineageType] = useState('Artifacts');
  const [selectedExecutionType, setSelectedExecutionType] = useState(null);
  const [lineageData, setLineageData]=useState(null);
  const [executionData, setExecutionData]=useState(null);
  const [lineageArtifactsKey, setLineageArtifactsKey] = useState(0);
  const [execDropdownData,setExecDropdownData] = useState([]);
  const [artitreeData, setArtiTreeData]=useState(null);

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
        fetchArtifactLineage(data[0]);
      }
    });
  };
  const handlePipelineClick = (pipeline) => {
    setLineageData(null);
    setExecutionData(null); 
    setArtiTreeData(null);
    setSelectedPipeline(pipeline);
    // when pipeline is updated we need to update the lineage selection too
    // this is also not needed as selectedLineage has default value
    // setSelectedLineageType(LineageTypes[0]);
     if (selectedPipeline) {
       if (selectedLineageType === "Artifacts") {
          //call artifact lineage as it is default
          fetchArtifactLineage(pipeline);
       }
       else if (selectedLineageType === "Execution" || selectedLineageType === "Tangled_Execution") {
          fetchExecutionTypes(pipeline, selectedLineageType);
       }
       else {
          
          fetchArtifactTree(pipeline, selectedLineageType);
      }}
  };

  const handleLineageTypeClick = (lineageType) => {
    setLineageData(null);
    setExecutionData(null);
    setArtiTreeData(null);
    setSelectedLineageType(lineageType);
    if (lineageType === "Artifacts") {
      fetchArtifactLineage(selectedPipeline);
    }
    else if (lineageType === "Execution" || lineageType === "Tangled_Execution" ) {
      fetchExecutionTypes(selectedPipeline, lineageType);
    }
    else {
      fetchArtifactTree(selectedPipeline, lineageType);
    }
  };  


  const fetchArtifactLineage = (pipelineName) => {
    client.getArtifactLineage(pipelineName).then((data) => {    
        if (data === null) { 
        setLineageData(null);
        }
        setLineageData(data);
    });
    setLineageArtifactsKey((prevKey) => prevKey + 1);
  };

  const fetchArtifactTree = (pipelineName,lineageType) => {
    client.getArtiTreeLineage(pipelineName,lineageType).then((data) => {    
    console.log(data,"fetchArtifact");
    if (data === null) { 
        setArtiTreeData(null);
    }
    setArtiTreeData(data);
    });
  };

  const fetchExecutionTypes = (pipelineName, lineageType) => {
    client.getExecutionTypes(pipelineName).then((data) => {    
        if (data === null ) {
           setExecDropdownData(null);
        }
        else {
        setExecDropdownData(data);
        setSelectedExecutionType(data[0]);     // data[0] = "Prepare_3f45"
        // method used such that even with multiple "_" it will get right execution_name and uuid
        const last_underscore_index = data[0].lastIndexOf('_'); 
        const exec_type = data[0].substring(0, last_underscore_index);   // Prepare
        const uuid= (data[0].split("_").pop());     // 3f45
        if (lineageType === "Execution") {
            fetchExecutionLineage(pipelineName, exec_type,uuid);
            }
        else {
            fetchExecTree(pipelineName,uuid);
            }
        }

    });
    setLineageArtifactsKey((prevKey) => prevKey + 1);
  };

  // used for execution drop down
  const handleExecutionClick = (executionType) => {
    setExecutionData(null);
    
    setSelectedExecutionType(executionType);
    const last_underscore_index = executionType.lastIndexOf('_');
    const exec_type = executionType.substring(0, last_underscore_index);
    const uuid= (executionType.split("_").pop());
    fetchExecutionLineage(selectedPipeline, exec_type,uuid);
  };  

  // used for execution drop down
  const handleTreeClick = (executionType) => {
    setExecutionData(null);
    setSelectedExecutionType(executionType);
    const uuid= (executionType.split("_").pop());
    fetchExecTree(selectedPipeline, uuid);
  };  

  const fetchExecutionLineage = (pipelineName, type,uuid) => {
    client.getExecutionLineage(pipelineName,type,uuid).then((data) => {    
      if (data === null) {
          setExecutionData(null);
      }
      setExecutionData(data);
    });
  };

  const fetchExecTree = (pipelineName,exec_type) => {
    client.getExecTreeLineage(pipelineName,exec_type).then((data) => {    
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
                {selectedPipeline !== null && selectedLineageType === "Artifacts" && lineageData !== null && (
                <LineageArtifacts key={lineageArtifactsKey}  data={lineageData}/>
              )}
                {selectedPipeline !== null && selectedLineageType === "Execution" && execDropdownData !== null  && executionData !== null &&(
                <div>
                <ExecutionDropdown data={execDropdownData} exec_type={selectedExecutionType} handleExecutionClick= {handleExecutionClick}/>        
                </div>
                )}
                {selectedPipeline !== null && selectedLineageType === "Execution" && execDropdownData !== null  && executionData !== null &&(
                <div>
                <LineageArtifacts key={lineageArtifactsKey} data={executionData} />
                </div>
                )}
                {selectedPipeline !== null && selectedLineageType === "Tangled_Execution" && execDropdownData !== null   &&(
                <div>
                <ExecutionTangledDropdown data={execDropdownData} exec_type={selectedExecutionType} handleTreeClick= {handleTreeClick}/>        
                </div>
                )}
                {selectedPipeline !== null && selectedLineageType === "Tangled_Execution" && execDropdownData !== null  && executionData !== null &&(
                <div style={{ justifyContent: 'center', alignItems: 'center' }}>
                <ExecutionTree key={lineageArtifactsKey} data={executionData} />
                </div>
                )}
                {selectedPipeline !== null && selectedLineageType === "Artifact_Tree" && artitreeData !== null &&(
                <div style={{ justifyContent: 'center', alignItems: 'center' }}>
                <TangledTree key={lineageArtifactsKey} data={artitreeData} />
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
