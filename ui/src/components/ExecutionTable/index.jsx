/* Comment out of the entire file as it has been recently edited */

// /***
//  * Copyright (2023) Hewlett Packard Enterprise Development LP
//  *
//  * Licensed under the Apache License, Version 2.0 (the "License");
//  * You may not use this file except in compliance with the License.
//  * You may obtain a copy of the License at
//  *
//  * http://www.apache.org/licenses/LICENSE-2.0
//  *
//  * Unless required by applicable law or agreed to in writing, software
//  * distributed under the License is distributed on an "AS IS" BASIS,
//  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  * See the License for the specific language governing permissions and
//  * limitations under the License.
//  ***/

// //ExecutionTable.jsx
// import React, { useState, useEffect } from "react";
// import "./index.module.css";
// import FastAPIClient from "../../client";
// import config from "../../config";
// import PythonEnvPopup from "../../components/PythonEnvPopup";

// const client = new FastAPIClient(config);

// const ExecutionTable = ({ executions, onSort, onFilter }) => {
//   // Default sorting order
//   const [sortOrder, setSortOrder] = useState(onSort);
//   const [sortedData, setSortedData] = useState([]);
//   // Local filter value state
//   const [filterValue, setFilterValue] = useState("");
//   const [expandedRow, setExpandedRow] = useState(null);

//   const [showPopup, setShowPopup] = useState(false);
//   const [popupData, setPopupData] = useState("");

//   const consistentColumns = [];

//   useEffect(() => {
//     // Set initial sorting order when component mounts
//     setSortedData([...executions]);
//   }, [executions]);

//   const handleSort = () => {
//     const newSortOrder =
//       sortOrder === "desc" ? "asc" : sortOrder === "asc" ? "desc" : "asc";
//     setSortOrder(newSortOrder);
//     const sorted = [...executions].sort((a, b) => {
//       if (newSortOrder === "asc") {
//         return a.Context_Type.localeCompare(b.Context_Type);
//       } else {
//         return b.Context_Type.localeCompare(a.Context_Type);
//       }
//     });
//     setSortedData(sorted); // Notify parent component about sorting change
//   };

//   const handleFilterChange = (event) => {
//     const value = event.target.value;
//     setFilterValue(value);
//     onFilter("Context_Type", value); // Notify parent component about filter change
//   };

//   const toggleRow = (rowId) => {
//     if (expandedRow === rowId) {
//       setExpandedRow(null);
//     } else {
//       setExpandedRow(rowId);
//     }
//   };

  
//   const handleLinkClick = (file_name) => {
//     setShowPopup(true);
//     client.getPythonEnv(file_name).then((data) => {
//       console.log(data);
//       setPopupData(data);
//       setShowPopup(true);
//     });
//   };

//   const handleClosePopup = () => {
//     setShowPopup(false);
//     setPopupData("");
//   };

//   const renderArrow = () => {
//     if (sortOrder === "desc") {
//       return (
//         <span
//           className="text-2xl cursor-pointer"
//           style={{ marginLeft: "4px", display: "inline-flex" }}
//         >
//           <svg
//             xmlns="http://www.w3.org/2000/svg"
//             width="16"
//             height="16"
//             fill="currentColor"
//             class="bi bi-arrow-down"
//             viewBox="0 0 16 16"
//           >
//             <path
//               fill-rule="evenodd"
//               d="M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1"
//             />
//           </svg>
//         </span>
//       ); //data is in desc order ---> ↓
//     } else if (sortOrder === "asc") {
//       return (
//         <span
//           className="text-2xl cursor-pointer"
//           style={{ marginLeft: "4px", display: "inline-flex" }}
//         >
//           <svg
//             xmlns="http://www.w3.org/2000/svg"
//             width="16"
//             height="16"
//             fill="currentColor"
//             class="bi bi-arrow-up"
//             viewBox="0 0 16 16"
//           >
//             <path
//               fill-rule="evenodd"
//               d="M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5"
//             />
//           </svg>
//         </span>
//       ); //data is in asc order ----> ↑
//     } else {
//       return (
//         <span
//           className="text-2xl cursor-pointer"
//           style={{ marginLeft: "4px", display: "inline-flex" }}
//         >
//           <svg
//             xmlns="http://www.w3.org/2000/svg"
//             width="16"
//             height="16"
//             fill="currentColor"
//             class="bi bi-arrow-down-up"
//             viewBox="0 0 16 16"
//           >
//             <path
//               fill-rule="evenodd"
//               d="M11.5 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L11 2.707V14.5a.5.5 0 0 0 .5.5m-7-14a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L4 13.293V1.5a.5.5 0 0 1 .5-.5"
//             />
//           </svg>
//         </span>
//       ); //data is in initial order -----------> ↓↑
//     }
//   };

//   return (
//     <div className="flex flex-col">
//       <div
//         style={{
//           display: "flex",
//           justifyContent: "flex-end",
//           marginBottom: "0.5rem",
//           marginTop: "0.5rem",
//         }}
//       >
//         <input
//           type="text"
//           value={filterValue}
//           onChange={handleFilterChange}
//           placeholder="Filter by Context Type"
//           style={{
//             marginRight: "1rem",
//             padding: "0.5rem",
//             border: "1px solid #ccc",
//           }}
//         />
//       </div>
//       <div className="overflow-x-auto">
//         <div className="p-1.5 w-full inline-block align-middle">
//           <table className="min-w-full divide-y divide-gray-200" id="mytable">
//             <thead>
//               <tr className="text-xs font-bold text-left text-black uppercase">
//                 <th scope="col" className="px-6 py-3"></th>
//                 <th scope="col" className="px-6 py-3">Execution uuid</th>
//                 <th
//                   scope="col"
//                   onClick={handleSort}
//                   className="px-6 py-3 Context_Type"
//                 >
//                   <span style={{ display: 'inline-flex', alignItems: 'center' }}>
//                     Context Type {renderArrow()}
//                   </span>
//                 </th>
//                 <th scope="col" className="px-6 py-3 Execution">
//                   Execution
//                 </th>
//                 <th scope="col" className="px-6 py-3 Env">
//                   <span style={{ display: 'inline-flex', alignItems: 'center' }}>
//                     Python Env
//                   </span>
//                 </th>
//                 <th scope="col" className="px-6 py-3 Git_Repo">
//                   Git Repo
//                 </th>
//                 <th scope="col" className="px-6 py-3 Git_Start_Commit">
//                   Git Start Commit
//                 </th>
//                 <th scope="col" className="px-6 py-3 Pipeline_Type">
//                   Pipeline Type
//                 </th>
//               </tr>
//             </thead>
//             <tbody className="body divide-y divide-gray-200">
//               {sortedData.map((data, index) => (
//                 <React.Fragment key={index}>
//                   <tr
//                     key={index}
//                     className="text-sm font-medium text-gray-800"
//                   >
//                     <td className="px-6 py-4 cursor-pointer"
//                       onClick={() => {toggleRow(index)}}
//                     >
//                       {expandedRow === index ? "-" : "+"}
//                     </td>
//                     <td className="px-6 py-4 break-words whitespace-normal max-w-xs">{data.Execution_uuid}</td>
//                     <td className="px-6 py-4">{data.Context_Type}</td>
//                     <td className="px-6 py-4">{data.Execution}</td>
//                     <td className="px-6 py-4">
//                           <a
//                             href="#"
//                             onClick={(e) => {
//                               e.preventDefault();
//                               handleLinkClick(data.custom_properties_Python_Env);
                    
//                             }}
//                           >
//                             View Env Details
//                           </a>
//                           <PythonEnvPopup
//                             show={showPopup}
//                             python_env={popupData}
//                             onClose={handleClosePopup}
//                           />
//                     </td>
//                     <td className="px-6 py-4">{data.Git_Repo}</td>
//                     <td className="px-6 py-4">{data.Git_Start_Commit}</td>
//                     <td className="px-6 py-4">{data.Pipeline_Type}</td>
//                   </tr>
//                   {expandedRow === index && (
//                     <tr>
//                       <td colSpan="4">
//                         <table className="expanded-table">
//                           <tbody>
//                             {Object.entries(data).map(([key, value]) => {
//                               if (
//                                 !consistentColumns.includes(key) &&
//                                 value != null
//                               ) {
//                                 return (
//                                   <React.Fragment key={key}>
//                                     <tr>
//                                       <td key={key}>{key}</td>
//                                       <td key={value} className="break-words whitespace-normal max-w-md">
//                                         {value ? value : "Null"}
//                                       </td>
//                                     </tr>
//                                   </React.Fragment>
//                                 );
//                               }
//                               return null;
//                             })}
//                           </tbody>
//                         </table>
//                       </td>
//                     </tr>
//                   )}
//                 </React.Fragment>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default ExecutionTable;
