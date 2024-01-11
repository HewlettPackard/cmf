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
import "./index.css";


const ArtifactTypeSidebar = ({ artifactTypes, handleArtifactTypeClick }) => {

  const [clickedArtifactType, setClickedArtifactType] = useState(artifactTypes[0]);

  useEffect(() => {
    handleClick(artifactTypes[0]);
    // eslint-disable-next-line     
  }, [artifactTypes]);

  const handleClick = (artifactType) => {
   setClickedArtifactType(artifactType);
   handleArtifactTypeClick(artifactType);
  };

  return (
    <div className="flex justify-between border-b border-gray-200">
       <div className="flex flex-row">
        {artifactTypes.map((artifactType, index) => (
            <button key={artifactType}
                  className={ clickedArtifactType  === artifactType
                            ? "art-tabs art-active-tabs"
                            : "art-tabs"}
                  onClick={() => handleClick(artifactType)}>
              {artifactType}
            </button>
        ))}
       </div>
    </div>
  );
};

export default ArtifactTypeSidebar;
