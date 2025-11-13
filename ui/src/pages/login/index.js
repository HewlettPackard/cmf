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
import { useAuth } from "../../contexts/AuthContext";
import { useNavigate, useSearchParams } from "react-router-dom";
import "./login.css";

const Login = () => {
  const { login, authenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Handle successful OAuth callback
  React.useEffect(() => {
    if (searchParams.get("auth") === "success") {
      // Redirect to home after successful login
      navigate("/");
    }
    
    // Handle authentication errors
    const error = searchParams.get("error");
    if (error === "unauthorized_domain") {
      alert("Your email domain is not authorized to access this application.");
    } else if (error === "auth_failed") {
      alert("Authentication failed. Please try again.");
    }
  }, [searchParams, navigate]);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (authenticated) {
      navigate("/");
    }
  }, [authenticated, navigate]);

  const handleGoogleLogin = () => {
    login();
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>CMF Server</h1>
          <p>Common Metadata Framework</p>
        </div>
        
        <div className="login-content">
          <h2>Sign in to continue</h2>
          
          <button 
            className="google-login-button" 
            onClick={handleGoogleLogin}
          >
            <svg className="google-icon" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Continue with Google
          </button>
          
          <p className="login-note">
            Sign in with your Google account to access the CMF Server dashboard.
          </p>
        </div>
        
        <div className="login-footer">
          <p>&copy; 2023 Hewlett Packard Enterprise Development LP</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
