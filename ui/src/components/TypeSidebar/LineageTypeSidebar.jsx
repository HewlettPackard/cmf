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

import { useState } from "react";

const LineageTypeSidebar = ({ LineageTypes, handleLineageTypeClick }) => {
  const [clickedLineageType, setClickedLineageType] = useState(LineageTypes[0]);

  const handleClick = (LineageType) => {
    // Do nothing if the tab is  already active
    if (clickedLineageType === LineageType) return;
    setClickedLineageType(LineageType);
    handleLineageTypeClick(LineageType);
  };

  return (
    <div className="flex justify-between border-b border-gray-200">
      <div className="flex flex-row">
        {LineageTypes.map((LineageType, index) => (
          <button
            key={LineageType}
            className={
              clickedLineageType === LineageType
                ? "art-tabs art-active-tabs"
                : "art-tabs"
            }
            onClick={() => handleClick(LineageType)}
          >
            {LineageType}
          </button>
        ))}
      </div>
    </div>
  );
};

export default LineageTypeSidebar;
