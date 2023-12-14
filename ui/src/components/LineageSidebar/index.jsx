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


const LineageSidebar = ({ pipelines, activeTab, handleClick }) => {
  return (
    <div className="sidebar flex flex-col bg-gray-100 pt-4 pr-4 pb-6 mb-12">
      <h1 className="px-6 pb-6 text-sm font-bold text-center text-gray-500 uppercase">
        List of Pipelines
      </h1>
      {pipelines.map((pipeline, index) => (
        <div key={index}>
          <button
            className={activeTab === index ? "tabs active-tabs" : "tabs"}
            onClick={() => handleClick(index)}
          >
            {pipeline}
          </button>
        </div>
      ))}
    </div>
  );
};

export default LineageSidebar;
