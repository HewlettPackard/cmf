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
import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import config from "../../config";
import FastAPIClient from "../../client";

const client = new FastAPIClient(config);

function OTPVerify() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  // ONE loading state + ONE action state
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState(""); // "verify" or "resend"

  useEffect(() => {
    if (!location.state?.email) navigate("/login");
    else setEmail(location.state.email);
  }, [location, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setAction("verify");  // mark button
    setLoading(true);

    try {
      const data = await client.verifyOTP(email, otp);
      login();
      alert("OTP Verified! Redirecting...");
      navigate("/home");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid OTP.");
    } finally {
      setLoading(false);
      setAction("");
    }
  };

  const resendOTP = async () => {
    setError("");
    setAction("resend");  // mark button
    setLoading(true);

    try {
      await client.sendOTP(email);
      alert(`A new OTP has been sent to ${email}.`);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to resend OTP.");
    } finally {
      setLoading(false);
      setAction("");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-6 rounded-2xl shadow-lg w-80">
        <h2 className="text-xl font-semibold mb-4 text-center">Verify OTP</h2>
        <p className="text-sm text-center text-gray-600 mb-3">
          OTP sent to <b>{email}</b>
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter OTP"
            className="w-full border rounded p-2 mb-2"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
          />
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          {/* VERIFY OTP BUTTON */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full p-2 rounded text-white 
              ${loading && action === "verify"
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-600 hover:bg-green-700"
              }`}
          >
            {loading && action === "verify" ? "Verifying..." : "Verify OTP"}
          </button>
          {/* RESEND OTP BUTTON */}
          <button
            type="button"
            disabled={loading}
            onClick={resendOTP}
            className={`w-full p-2 rounded text-white mt-2 
              ${loading && action === "resend"
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-gray-600 hover:bg-gray-700"
              }`}
          >
            {loading && action === "resend" ? "Resending..." : "Resend OTP"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default OTPVerify;
