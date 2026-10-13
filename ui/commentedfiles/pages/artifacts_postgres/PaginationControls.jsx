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

// const PaginationControls = ({
//   totalItems,
//   activePage,
//   clickedButton,
//   onPageClick,
//   onPrevClick,
//   onNextClick
// }) => {
//   const totalPages = Math.ceil(totalItems / 5);

//   if (totalItems === 0) {
//     return null;
//   }

//   return (
//     <div className="pagination-controls">
//       <button
//         onClick={onPrevClick}
//         disabled={activePage === 1}
//         className={clickedButton === "prev" ? "active-page" : ""}
//       >
//         Previous
//       </button>
      
//       {Array.from({ length: totalPages }).map((_, index) => {
//         const pageNumber = index + 1;
        
//         if (
//           pageNumber === 1 ||
//           pageNumber === totalPages
//         ) {
//           return (
//             <button
//               key={pageNumber}
//               onClick={() => onPageClick(pageNumber)}
//               className={`pagination-button ${
//                 activePage === pageNumber && clickedButton === "page"
//                   ? "active-page"
//                   : ""
//               }`}
//             >
//               {pageNumber}
//             </button>
//           );
//         } else if (
//           (activePage <= 3 && pageNumber <= 6) ||
//           (activePage >= totalPages - 2 && pageNumber >= totalPages - 5) ||
//           Math.abs(pageNumber - activePage) <= 2
//         ) {
//           return (
//             <button
//               key={pageNumber}
//               onClick={() => onPageClick(pageNumber)}
//               className={`pagination-button ${
//                 activePage === pageNumber && clickedButton === "page"
//                   ? "active-page"
//                   : ""
//               }`}
//             >
//               {pageNumber}
//             </button>
//           );
//         } else if (
//           (pageNumber === 2 && activePage > 3) ||
//           (pageNumber === totalPages - 1 && activePage < totalPages - 3)
//         ) {
//           return (
//             <span
//               key={`ellipsis-${pageNumber}`}
//               className="ellipsis"
//             >
//               ...
//             </span>
//           );
//         }
//         return null;
//       })}
      
//       <button
//         onClick={onNextClick}
//         disabled={activePage === totalPages}
//         className={clickedButton === "next" ? "active-page" : ""}
//       >
//         Next
//       </button>
//     </div>
//   );
// };

// export default PaginationControls;
