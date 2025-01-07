import React, { useState, useEffect } from "react";
import "./index.css"; // Import the CSS file
import FastAPIClient from "../../client";
import config from "../../config";

// Correctly declare the client
const client = new FastAPIClient(config);

function Search() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState("");

  // UseEffect should have an empty dependency array to only run on mount
  useEffect(() => {
    // Optional: you can perform an initial API call here if needed
    client.getSearchResult("").then((data) => {
      setData(data);
    });
  }, []); // This ensures it only runs once on mount

  const handleSubmit = () => {
    client.getSearchResult(query).then((data) => {
      setData(data);
      // console.log(data); // You can see the response in the console
    });
  };

  return (
    <div className="container">
      <div className="searchBox">
        <input
          type="text"
          placeholder="Type here.."
          value={query}
          onChange={(e) => setQuery(e.target.value)} // Handle input change
          className="input"
        />
        <button onClick={handleSubmit} className="button">
          Search
        </button>
      </div>

      <div className="api-data">
        <h3>API Response:</h3>
        <pre>{JSON.stringify(data, null, 2)}</pre> {/* Displaying the data as JSON */}
      </div>
    </div>
  );
}

export default Search;
