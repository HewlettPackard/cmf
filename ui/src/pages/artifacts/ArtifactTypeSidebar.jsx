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
