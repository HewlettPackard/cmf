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

import React, { useState, useEffect } from "react";

const ExecutionTangledDropdown = ({ data, exec_type, handleTreeClick }) => {
  const [selectedExecutionType, setSelectedExecutionType] = useState("");

  useEffect(() => {
    if (exec_type) {
      setSelectedExecutionType(exec_type);
    }
  }, [exec_type]);

  const handleCallExecutionClick = (event) => {
    handleTreeClick(event.target.value);
  };

  return (
    <div className="flex items-center gap-3 mt-4">
      <label className="text-sm font-semibold text-gray-700 whitespace-nowrap">Execution list:</label>
      <div className="relative">
        <select
          className="appearance-none bg-white border-2 border-teal-400 hover:border-teal-600 focus:border-teal-600 focus:ring-2 focus:ring-teal-200 rounded-lg py-2 pl-4 pr-8 text-sm font-medium text-gray-800 cursor-pointer shadow-sm outline-none transition-all duration-200"
          value={selectedExecutionType}
          onChange={(event) => {
            handleCallExecutionClick(event);
          }}
        >
          {data.map((type, index) => (
            <option key={index} value={type}>
              {type}
            </option>
          ))}
        </select>
        {/* Dropdown Icon */}
        <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
          <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default ExecutionTangledDropdown;
