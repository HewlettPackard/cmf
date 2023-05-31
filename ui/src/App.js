import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import Artifacts from "./pages/artifacts";
import Executions from "./pages/executions";
import Lineage from "./pages/lineage";
import "./App.css";

function App() {
  return (
    <div className="App bg-white max-w-screen overflow-x-hidden">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route exact path="/display_artifacts" element={<Artifacts />} />
          <Route exact path="/display_executions" element={<Executions />} />
          <Route exact path="/display_lineage" element={<Lineage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
