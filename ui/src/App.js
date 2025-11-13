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
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/home";
import Login from "./pages/login";
import Lineage from "./pages/lineage";
import TensorBoard from "./pages/tensorboard";
import Metahub from "./pages/metahub";
import "./App.css";
import ArtifactsPostgres from "./pages/artifacts_postgres";
import ExecutionsPostgres from "./pages/executions_postgres";

function App() {
  return (
    <div className="App bg-white">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route
              exact
              path="/artifacts"
              element={
                <ProtectedRoute>
                  <ArtifactsPostgres />
                </ProtectedRoute>
              }
            />
            <Route
              exact
              path="/executions"
              element={
                <ProtectedRoute>
                  <ExecutionsPostgres />
                </ProtectedRoute>
              }
            />
            <Route
              exact
              path="/display_lineage"
              element={
                <ProtectedRoute>
                  <Lineage />
                </ProtectedRoute>
              }
            />
            <Route
              exact
              path="/tensorboard"
              element={
                <ProtectedRoute>
                  <TensorBoard />
                </ProtectedRoute>
              }
            />
            <Route
              exact
              path="/metahub"
              element={
                <ProtectedRoute>
                  <Metahub />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
