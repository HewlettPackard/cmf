// Comment out of the entire file as it has been recently edited
// and moved to a new file named artifacts_postgres_grid.

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

// import React from "react";
// import Loader from "../../../components/Loader";

// const LabelContentPanel = ({
//   selectedTableLabel,
//   labelContentLoading,
//   labelData,
//   parsedLabelData,
//   labelColumns,
//   currentPage,
//   rowsPerPage,
//   setCurrentPage,
//   setRowsPerPage
// }) => {
//   if (!selectedTableLabel) {
//     return (
//       <div className="p-4">
//         <div className="flex justify-center items-center py-12">
//           <div className="text-center">
//             <h3 className="text-xl font-medium text-gray-800 mb-2">
//               Select a Label
//             </h3>
//             <p className="text-gray-600">
//               Click on a label name in the table to view its content
//             </p>
//           </div>
//         </div>
//       </div>
//     );
//   }

//   if (labelContentLoading) {
//     return (
//       <div className="p-4">
//         <div className="flex justify-center items-center py-12">
//             <Loader />
//           </div>
//       </div>
//     );
//   }

//   if (!labelData) {
//     return (
//       <div className="p-4">
//         <div className="text-center py-12">
//           <p className="text-gray-600">No content available</p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="p-4">
//       <div className="h-full flex flex-col">
//         {/* Header aligned with left table */}
//         <div className="p-4 border-b border-gray-200">
//           <div className="flex justify-between items-center">
//             <h3 className="text-lg font-medium text-gray-900">
//               {selectedTableLabel.name.split(":")[1] || selectedTableLabel.name}
//             </h3>
//             {selectedTableLabel?.isSearchResult && selectedTableLabel?.searchFilter && (
//               <span className="text-sm text-blue-600 bg-blue-50 px-3 py-1 rounded">
//                 Filtered: {selectedTableLabel.searchFilter}
//               </span>
//             )}
//           </div>
//         </div>

//         {/* Fixed size table container */}
//         <div className="flex flex-col" style={{ height: '400px' }}>
//           <div className="overflow-auto bg-white border border-gray-300 rounded" style={{ height: '320px' }}>
//             <table className="divide-y divide-gray-200 border-4 w-full">
//               <thead className="sticky top-0">
//                 <tr className="text-xs font-bold font-sans text-left text-black uppercase">
//                   {labelColumns.map((column, index) => (
//                     <th
//                       key={index}
//                       scope="col"
//                       className="px-6 py-3"
//                     >
//                       {column.name}
//                     </th>
//                   ))}
//                 </tr>
//               </thead>
//               <tbody className="bg-white divide-y divide-gray-200">
//                 {parsedLabelData.slice(currentPage * rowsPerPage, (currentPage + 1) * rowsPerPage).map((row, rowIndex) => (
//                   <tr key={rowIndex} className="text-sm font-medium text-gray-800">
//                     {labelColumns.map((column, colIndex) => (
//                       <td key={colIndex} className="px-6 py-4">
//                         {String(row[column.name] || '')}
//                       </td>
//                     ))}
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>

//           {/* Pagination controls */}
//           <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-t border-gray-200">
//             <div className="flex items-center space-x-2">
//               <span className="text-sm text-gray-700">Rows per page:</span>
//               <select
//                 value={rowsPerPage}
//                 onChange={(e) => {
//                   setRowsPerPage(Number(e.target.value));
//                   setCurrentPage(0);
//                 }}
//                 className="border border-gray-300 rounded px-2 py-1 text-sm"
//               >
//                 <option value={10}>10</option>
//                 <option value={25}>25</option>
//                 <option value={50}>50</option>
//                 <option value={100}>100</option>
//               </select>
//             </div>

//             <div className="flex items-center space-x-2">
//               <span className="text-sm text-gray-700">
//                 {currentPage * rowsPerPage + 1}-{Math.min((currentPage + 1) * rowsPerPage, parsedLabelData.length)} of {parsedLabelData.length}
//               </span>
//               <button
//                 onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
//                 disabled={currentPage === 0}
//                 className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
//               >
//                 Previous
//               </button>
//               <button
//                 onClick={() => setCurrentPage(Math.min(Math.ceil(parsedLabelData.length / rowsPerPage) - 1, currentPage + 1))}
//                 disabled={currentPage >= Math.ceil(parsedLabelData.length / rowsPerPage) - 1}
//                 className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
//               >
//                 Next
//               </button>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default LabelContentPanel;
