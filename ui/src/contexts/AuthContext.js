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

import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import config from "../config";

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${config.apiBasePath}/auth/me`, {
        withCredentials: true, // Important: include cookies
      });
      
      if (response.data.authenticated) {
        setUser(response.data.user);
        setAuthenticated(true);
      } else {
        setUser(null);
        setAuthenticated(false);
      }
    } catch (error) {
      console.error("Error checking auth status:", error);
      setUser(null);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    // Redirect to Google OAuth login
    window.location.href = `${config.apiBasePath}/auth/login/google`;
  };

  const logout = async () => {
    try {
      await axios.post(`${config.apiBasePath}/auth/logout`, {}, {
        withCredentials: true,
      });
      setUser(null);
      setAuthenticated(false);
      window.location.href = "/"; // Redirect to home
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  const value = {
    user,
    loading,
    authenticated,
    login,
    logout,
    checkAuthStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
