import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import config from "../../config";

function Login() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const validateEmail = (email) => /\S+@\S+\.\S+/.test(email);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setError("");

    try {
      const response = await fetch(`${config.apiBasePath}/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient_email: email }),
      });

      if (response.ok) {
        alert(`OTP sent to ${email}`);
        navigate("/otp", { state: { email } });
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to send OTP");
      }
    } catch (err) {
      setError("Server error. Please try again later.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-6 rounded-2xl shadow-lg w-80">
        <h2 className="text-xl font-semibold mb-4 text-center">Login</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Enter your email"
            className="w-full border rounded p-2 mb-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
          >
            Send OTP
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
