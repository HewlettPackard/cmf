import React, { useState } from "react";
import "./index.css";


const ArtifactTypeSidebar = ({ artifactTypes, handleArtifactTypeClick }) => {

  /*const [clickedArtifactType, setClickedArtifactType] = useState(artifactTypes[0]);*/
  const [toggleState, setToggleState] = useState(0);

  /*useEffect(() => {
    handleClick(artifactTypes[0]);
     
  }, []);*/

  const handleClick = (artifactType, i ) => {
 /*  setClickedArtifactType(artifactType);*/
   setToggleState(i);
   handleArtifactTypeClick(artifactType);
  };

  return (
    <div className="flex justify-between border-b border-gray-200">
      <ul>
       <div className="flex flex-row">
        {artifactTypes.map((artifactType, index) => (
          <li key={index}>
            <button key={artifactType}
                  className={ toggleState  === index
                            ? "art-tabs art-active-tabs"
                            : "art-tabs"}
                  onClick={() => handleClick(artifactType, index)}>
              {artifactType}
            </button>
          </li>
        ))}
       </div>
      </ul>
    </div>
  );
};

export default ArtifactTypeSidebar;
