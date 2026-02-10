/***
 * Copyright (2025) Hewlett Packard Enterprise Development LP
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

// Creating a global authentication context
const AuthContext = createContext();

// Custom hook to use the AuthContext
export const useAuth = () => {
    // Access the AuthContext to get authentication state and actions
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

// Here children = anything inside <AuthProvider> ... </AuthProvider>
export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is authenticated (stored in localStorage)
        const authStatus = localStorage.getItem("isAuthenticated");
        setIsAuthenticated(authStatus === "true");
        setLoading(false);
    }, []);

    const login = () => {
        localStorage.setItem("isAuthenticated", "true");
        setIsAuthenticated(true);
    };

    const logout = () => {
        localStorage.removeItem("isAuthenticated");
        setIsAuthenticated(false);
    };

    // Provides the context value to all children components
    return (
        <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
