/***
 * Example of how to add UserProfile component to your page headers
 * 
 * You can integrate this into any of your existing page components
 * by adding the UserProfile component to your navigation or header area
 ***/

import React from "react";
import UserProfile from "../components/UserProfile";

const ExamplePageWithUserProfile = () => {
  return (
    <div>
      {/* Your page header/navigation */}
      <header style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center", 
        padding: "16px 24px",
        borderBottom: "1px solid #e0e0e0",
        backgroundColor: "white"
      }}>
        <h1>CMF Server</h1>
        
        {/* Add UserProfile component here */}
        <UserProfile />
      </header>

      {/* Your page content */}
      <main>
        <p>Your page content goes here</p>
      </main>
    </div>
  );
};

export default ExamplePageWithUserProfile;
