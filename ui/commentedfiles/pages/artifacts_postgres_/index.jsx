// Comment out of the entire file as it has been recently edited 
// and moved to a new file named artifacts_postgres_grid. 
// The new file has the same code with some additions for grid view implementation.

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

// import React, { useEffect, useState } from "react";
// import FastAPIClient from "../../client";
// import config from "../../config";
// import DashboardHeader from "../../components/DashboardHeader";
// import ArtifactPTable from "../../components/ArtifactPTable";
// import Footer from "../../components/Footer";
// import "./index.css";
// import Sidebar from "../../components/Sidebar";
// import ArtifactTypeSidebar from "../../components/ArtifactTypeSidebar";
// import LabelContentPanel from "./components/LabelContentPanel";
// import ResizableSplitPane from "../../components/ResizableSplitPane";
// import PaginationControls from "./components/PaginationControls";
// import Papa from "papaparse";

// const client = new FastAPIClient(config);

// const ArtifactsPostgres = () => {
//   const [selectedPipeline, setSelectedPipeline] = useState(null);
//   const [pipelines, setPipelines] = useState([]);
//   // undefined state is to check whether artifacts data is set
//   // null state of artifacts we display No Data
//   const [artifacts, setArtifacts] = useState([]);
//   const [artifactTypes, setArtifactTypes] = useState([]);
//   const [selectedArtifactType, setSelectedArtifactType] = useState(null);
//   const [filter, setFilter] = useState("");
//   const [sortOrder, setSortOrder] = useState("asc");
//   const [totalItems, setTotalItems] = useState(0);
//   const [activePage, setActivePage] = useState(1);
//   const [clickedButton, setClickedButton] = useState("page"); 
//   const [selectedCol, setSelectedCol] = useState("name");
  
//   // Label content panel states
//   const [selectedTableLabel, setSelectedTableLabel] = useState(null);
//   const [labelContentLoading, setLabelContentLoading] = useState(false);
//   const [labelData, setLabelData] = useState(null);
//   const [parsedLabelData, setParsedLabelData] = useState([]);
//   const [labelColumns, setLabelColumns] = useState([]);
//   const [labelCurrentPage, setLabelCurrentPage] = useState(0);
//   const [labelRowsPerPage, setLabelRowsPerPage] = useState(10);
  
//   useEffect(() => {
//     fetchPipelines(); // Fetch pipelines and artifact types when the component mounts
//   },[]);

//   // Fetch pipelines on component mount
//   const fetchPipelines = () => {
//     client.getPipelines("").then((data) => {
//       setPipelines(data);
//       const defaultPipeline = data[0];
//       setSelectedPipeline(defaultPipeline); // Set the first pipeline as default
//     });
//   };  
  
//   useEffect(() => {
//     if (selectedPipeline){
//       fetchArtifactTypes(selectedPipeline);
//     }
//   },[selectedPipeline]);
  
//   const fetchArtifactTypes = () => {
//     client.getArtifactTypes().then((types) => {
//       setArtifactTypes(types);
//       const defaultArtifactType = types[0];
//       setSelectedArtifactType(defaultArtifactType); // Set the first artifact type as default
//       fetchArtifacts(selectedPipeline, defaultArtifactType, sortOrder, activePage, filter, selectedCol); // Fetch artifacts for the first artifact type and default pipeline
//     });  
//   };  
 
//   useEffect(() => {
//     if ( selectedPipeline && selectedArtifactType ){
//       fetchArtifacts(selectedPipeline, selectedArtifactType, sortOrder, activePage, filter, selectedCol);
//     }
//   }, [selectedArtifactType, sortOrder, activePage, selectedCol, filter]);

//   const fetchArtifacts = (pipelineName, artifactType, sortOrder, activePage, filter="", selectedCol) => {
//     client.getArtifacts(pipelineName, artifactType, sortOrder, activePage, filter, selectedCol)
//       .then((data) => {
//         setArtifacts(data.items);
//         setTotalItems(data.total_items);
//       });  
//   };    
  
//   const handleArtifactTypeClick = (artifactType) => {
//     if (selectedArtifactType !== artifactType) {
//       // if same artifact type is not clicked, sets page as null until it retrieves data for that type.
//       setArtifacts(null);
//       // Reset label panel state when switching artifact types
//       setSelectedTableLabel(null);
//       setLabelData(null);
//       setParsedLabelData([]);
//       setLabelColumns([]);
//     }  
//     setSelectedArtifactType(artifactType);
//     setActivePage(1);
//   };  

//   const handlePipelineClick = (pipeline) => {
//     if (selectedPipeline !== pipeline) {
//       // this condition sets page as null.
//       setArtifacts(null);
//     }  
//     setSelectedPipeline(pipeline);
//     setActivePage(1);
//   };  

//   const handleFilter = (value) => {
//     setFilter(value); // Update the filter string
//     setActivePage(1);
//  };   

//   const toggleSortOrder = (newSortOrder) => {
//     setSortOrder(newSortOrder);
//     setSelectedCol("name");
//   };  

//   const toggleSortTime = (newSortOrder) => {
//     setSortOrder(newSortOrder);
//     setSelectedCol("create_time_since_epoch");
//   };  

//   const handlePageClick = (page) => {
//     setActivePage(page);
//     setClickedButton("page");
//   };  

//   const handlePrevClick = () => {
//     if (activePage > 1) {
//       setActivePage(activePage - 1);
//       setClickedButton("prev");
//       handlePageClick(activePage - 1);
//     }  
//   };  

//   const handleNextClick = () => {
//     if (activePage < Math.ceil(totalItems / 5)) {
//       setActivePage(activePage + 1);
//       setClickedButton("next");
//       handlePageClick(activePage + 1);
//     }  
//   };

//   const handleLabelClick = (labelName, artifact) => {
//     setSelectedTableLabel({ name: labelName, ...artifact });
//     setLabelContentLoading(true);
//     setLabelCurrentPage(0); // Reset to first page
    
//     // Extract UUID from labelName (format: "path/to/labels.csv:uuid" or just "uuid")
//     const labelId = labelName.includes(":") ? labelName.split(":")[1] : labelName;
    
//     client.getLabelData(labelId).then((csvData) => {
//       setLabelData(csvData);
//       console.log("label CSV data = ", csvData);
      
//       // Parse CSV data using Papa.parse
//       if (csvData && typeof csvData === 'string' && csvData.trim().length > 0) {
//         const parsed = Papa.parse(csvData, { header: true });
//         console.log("parsed data = ", parsed.data);
        
//         if (parsed.data && parsed.data.length > 0) {
//           setParsedLabelData(parsed.data);
          
//           // Extract columns from Papa.parse meta fields
//           if (parsed.meta.fields) {
//             const columns = parsed.meta.fields.map(field => ({ name: field }));
//             console.log("columns = ", columns);
//             setLabelColumns(columns);
//           }
//         } else {
//           console.warn("Parsed CSV data is empty");
//           setParsedLabelData([]);
//           setLabelColumns([]);
//         }
//       } else {
//         console.warn("No CSV data received from getLabelData");
//         setParsedLabelData([]);
//         setLabelColumns([]);
//       }
//       setLabelContentLoading(false);
//     }).catch((error) => {
//       console.error("Error fetching label data:", error);
//       setLabelContentLoading(false);
//       setParsedLabelData([]);
//       setLabelColumns([]);
//     });
//   };  

//   return (
//     <>
//       <section
//         className="flex flex-col bg-white min-h-screen"
//         style={{ minHeight: "100vh" }}
//       >
//         <DashboardHeader />
//         <div className="flex flex-grow" style={{ padding: "1px" }}>
//           <div className="sidebar-container min-h-140 bg-gray-100 pt-2 pr-2 pb-4 w-1/6 flex-grow-0">
//             <Sidebar
//               pipelines={pipelines}
//               handlePipelineClick={handlePipelineClick}
//               className="flex-grow"
//             />
//           </div>
//           <div className="w-5/6 justify-center items-center mx-auto px-4 flex-grow">
//             <div className="flex flex-col w-full">
//                 {selectedPipeline !== null && (
//                   <ArtifactTypeSidebar
//                     artifactTypes={artifactTypes}
//                     handleArtifactTypeClick={handleArtifactTypeClick}
//                     onFilter={handleFilter}
//                   />
//                 )}
//             </div>
//             {selectedArtifactType === "Label" ? (
//               // Resizable split view for Label artifact type
//               <ResizableSplitPane
//                 initialSplitPercentage={50}
//                 minPercentage={30}
//                 maxPercentage={70}
//                 leftContent={
//                   <div>
//                     {artifacts !== null && artifacts.length > 0 ? (
//                       <>
//                         <ArtifactPTable 
//                           artifacts={artifacts}
//                           artifactType={selectedArtifactType}
//                           onsortOrder={toggleSortOrder}
//                           onsortTimeOrder={toggleSortTime}
//                           filterValue={filter}
//                           onLabelClick={handleLabelClick}
//                         />
//                         <PaginationControls
//                           totalItems={totalItems}
//                           activePage={activePage}
//                           clickedButton={clickedButton}
//                           onPageClick={handlePageClick}
//                           onPrevClick={handlePrevClick}
//                           onNextClick={handleNextClick}
//                         />
//                       </>
//                     ) : (
//                       <div>No data available</div>
//                     )}
//                   </div>
//                 }
//                 rightContent={
//                   <LabelContentPanel
//                     selectedTableLabel={selectedTableLabel}
//                     labelContentLoading={labelContentLoading}
//                     labelData={labelData}
//                     parsedLabelData={parsedLabelData}
//                     labelColumns={labelColumns}
//                     currentPage={labelCurrentPage}
//                     rowsPerPage={labelRowsPerPage}
//                     setCurrentPage={setLabelCurrentPage}
//                     setRowsPerPage={setLabelRowsPerPage}
//                   />
//                 }
//               />
//             ) : (
//               // Standard view for other artifact types
//               <div>
//                 {artifacts !== null && artifacts.length > 0 ? (
//                   <ArtifactPTable 
//                     artifacts={artifacts}
//                     artifactType={selectedArtifactType}
//                     onsortOrder={toggleSortOrder}
//                     onsortTimeOrder={toggleSortTime}
//                     filterValue={filter}
//                     />
                    
//                 ) : (
//                   <div>No data available</div> // Display message when there are no artifacts
//                 )}
//                 <PaginationControls
//                   totalItems={totalItems}
//                   activePage={activePage}
//                   clickedButton={clickedButton}
//                   onPageClick={handlePageClick}
//                   onPrevClick={handlePrevClick}
//                   onNextClick={handleNextClick}
//                 />
//               </div>
//             )}
//           </div>
//         </div>
//         <Footer />
//       </section>
//     </>
//   );
// };
// export default ArtifactsPostgres;
