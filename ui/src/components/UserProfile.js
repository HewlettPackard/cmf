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

// import React, { useState } from "react";
// import { useAuth } from "../contexts/AuthContext";
// import "./UserProfile.css";

// const UserProfile = () => {
//   const { user, logout } = useAuth();
//   const [showMenu, setShowMenu] = useState(false);

//   if (!user) return null;

//   const toggleMenu = () => setShowMenu(!showMenu);

//   return (
//     <div className="user-profile">
//       <div className="user-profile-trigger" onClick={toggleMenu}>
//         <img 
//           src={user.picture || "/default-avatar.png"} 
//           alt={user.name}
//           className="user-avatar"
//         />
//         <span className="user-name">{user.name}</span>
//         <svg 
//           className={`dropdown-arrow ${showMenu ? "open" : ""}`}
//           width="12" 
//           height="12" 
//           viewBox="0 0 12 12"
//         >
//           <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
//         </svg>
//       </div>

//       {showMenu && (
//         <>
//           <div className="user-profile-overlay" onClick={toggleMenu} />
//           <div className="user-profile-menu">
//             <div className="user-info">
//               <img 
//                 src={user.picture || "/default-avatar.png"} 
//                 alt={user.name}
//                 className="user-avatar-large"
//               />
//               <div className="user-details">
//                 <div className="user-name-large">{user.name}</div>
//                 <div className="user-email">{user.email}</div>
//               </div>
//             </div>
            
//             <div className="menu-divider" />
            
//             <button className="logout-button" onClick={logout}>
//               <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
//                 <path d="M3 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H3zm8 11.5a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1 0-1h7a.5.5 0 0 1 .5.5zM3 4.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5z"/>
//               </svg>
//               Sign Out
//             </button>
//           </div>
//         </>
//       )}
//     </div>
//   );
// };

// export default UserProfile;
