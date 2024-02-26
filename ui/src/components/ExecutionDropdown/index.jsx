import React, { useState } from "react";

const ExecutionDropdown = ({data,handleExecutionClick}) => {
   const [selectedExecutionType, setSelectedExecutionType] = useState('');
   const [execTypes,setExecTypes]= useState([]);
   const handleExecutionTypeSelect = (event) => {
       setSelectedExecutionType(event.target.value);
       handleExecutionClick(event.target.value);
   };
   return (
     <div className= "dropdown">  
      <select 
        className= "dropdown-select"
        onChange={handleExecutionTypeSelect}
      > 
        {data.map((type, index) => {
         return (
         <option key={index} value={type}> 
             {type}
         </option>
         );
         })}
       </select>
       <p>{selectedExecutionType}</p>
      </div>

  );
};

export default ExecutionDropdown;

