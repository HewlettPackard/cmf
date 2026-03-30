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
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/home";
import Lineage from "./pages/lineage";
import TensorBoard from "./pages/tensorboard";
import Metahub from "./pages/metahub";
import ArtifactsPostgres from "./pages/artifacts_postgres";
import ExecutionsPostgres from "./pages/executions_postgres";
import Login from "./pages/authentication/login";
import OTPVerify from "./pages/authentication/otp";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import "./App.css";

function App() {
  return (
    <div className="App bg-white">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/login" />} />

            <Route path="/login" element={<Login />} />
            <Route path="/otp" element={<OTPVerify />} />

            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route
              path="/artifacts"
              element={
                <ProtectedRoute>
                  <ArtifactsPostgres />
                </ProtectedRoute>
              }
            />
            <Route
              path="/executions"
              element={
                <ProtectedRoute>
                  <ExecutionsPostgres />
                </ProtectedRoute>
              }
            />
            <Route
              path="/display_lineage"
              element={
                <ProtectedRoute>
                  <Lineage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tensorboard"
              element={
                <ProtectedRoute>
                  <TensorBoard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/metahub"
              element={
                <ProtectedRoute>
                  <Metahub />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
