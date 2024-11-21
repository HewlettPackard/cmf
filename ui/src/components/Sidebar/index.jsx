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

// Sidebar.js

import React, { useState } from "react";
import "./index.css";

const Sidebar = ({ pipelines, handlePipelineClick }) => {
  /*const [clickedPipeline, setClickedPipeline] = useState(pipelines[0] || '')*/
  const [toggleState, setToggleState] = useState(0);

  /* useEffect(() => {
    handleClick(pipelines[0]);
  }, []);*/

  const handleClick = (pipeline, i) => {
    /*setClickedPipeline(pipeline);*/
    setToggleState(i);
    handlePipelineClick(pipeline);
  };

  return (
    <div className="flex flex-col ">
      <h1 className="px-2 py-4 text-base font-bold text-center border-b-4 border-black  uppercase">
        {" "}
        List of Pipelines{" "}
      </h1>
      <div className="sidebar">
        <ul>
          {pipelines.map((pipeline, index) => (
            <li key={index}>
              <a
                href="#"
                className={
                  toggleState === index
                    ? "side-tabs side-active-tabs"
                    : "side-tabs"
                }
                onClick={() => handleClick(pipeline, index)}
              >
                {pipeline}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Sidebar;
