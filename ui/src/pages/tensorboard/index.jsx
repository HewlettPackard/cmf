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

const client = new FastAPIClient(config);

const TensorBoard = () => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);

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

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-row">
          <Sidebar
            pipelines={pipelines}
            handlePipelineClick={handlePipelineClick}
          />
          <div className="container justify-center items-center mx-auto px-4">
            <iframe
              title="Example Iframe"
              src="http://10.93.244.204:6006/"
              allowFullScreen
              width="100%" height="1200"
            />
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default TensorBoard;
