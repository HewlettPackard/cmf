/***
* Copyright (2023) Hewlett Packard Enterprise Development LP
*
* Licensed under the Apache License, Version 2.0 (the "License");
* You may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
***/

import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import Artifacts from "./pages/artifacts";
import Executions from "./pages/executions";
import Lineage from "./pages/lineage";
import TensorBoard from "./pages/tensorboard";
import "./App.css";

function App() {
  return (
    <div className="App bg-white max-w-screen ">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route exact path="/artifacts" element={<Artifacts />} />
          <Route exact path="/executions" element={<Executions />} />
          <Route exact path="/display_lineage" element={<Lineage />} />
          <Route exact path="/tensorboard" element={<TensorBoard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
