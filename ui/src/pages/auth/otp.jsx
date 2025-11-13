import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import config from "../../config";

function OTPVerify() {
  const location = useLocation();
  const navigate = useNavigate();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!location.state?.email) navigate("/login");
    else setEmail(location.state.email);
  }, [location, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${config.apiBasePath}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient_email: email, otp }),
      });

      if (response.ok) {
        alert("OTP Verified! Redirecting...");
        navigate("/home");
      } else {
        const data = await response.json();
        setError(data.detail || "Invalid OTP. Please try again.");
      }
    } catch (err) {
      setError("Server error. Please try again later.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-6 rounded-2xl shadow-lg w-80">
        <h2 className="text-xl font-semibold mb-4 text-center">Verify OTP</h2>
        <p className="text-sm mb-2 text-gray-600 text-center">
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
          <button
            type="submit"
            className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700"
          >
            Verify OTP
          </button>
          <button
            type="button"
            className="w-full bg-gray-600 text-white p-2 rounded hover:bg-gray-700 mt-2"
            onClick={() => navigate("/login")}
          >
            Back to Login
          </button>
        </form>
      </div>
    </div>
  );
}

export default OTPVerify;
