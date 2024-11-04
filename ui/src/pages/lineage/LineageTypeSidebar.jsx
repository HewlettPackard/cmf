import React, { useState } from "react";
import "./index.css";

const LineageTypeSidebar = ({ LineageTypes, handleLineageTypeClick }) => {
  const [clickedLineageType, setClickedLineageType] = useState(LineageTypes[0]);

  const handleClick = (LineageType) => {
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
