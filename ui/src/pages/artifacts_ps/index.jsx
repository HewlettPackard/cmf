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

const client = new FastAPIClient(config);

const Artifacts_ps = () => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  // undefined state is to check whether artifacts data is set
  // null state of artifacts we display No Data
  const [artifacts, setArtifacts] = useState([]);
 

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };

  useEffect(() => {
    fetchPipelines();
    fetchArtifacts();
  }, []);

  const handlePipelineClick = (pipeline) => {
    if (selectedPipeline !== pipeline) {
      // this condition sets page as null.
      setArtifacts(null);
    }
    setSelectedPipeline(pipeline);
  };

  const fetchArtifacts = () => {
      client.getArtifact()
      .then((data) => {
        setArtifacts(data);
        //console.log(data)
      })
      //console.log(artifacts);
      //console.log("everyone is crazy!!!!!!!!!!");
  };

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
            <div>
              {(
                  <ArtifactPsTable
                    artifacts={artifacts}
                  />
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
