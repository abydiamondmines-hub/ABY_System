import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "./AuthComponents/AuthLayout";
import AuthCard from "./AuthComponents/AuthCard";
import Logo from "./AuthComponents/Logo";
import InputField from "./AuthComponents/InputField";
import AuthButton from "./AuthComponents/AuthButton";
import api from "../api";

const Mfa = () => {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [message, setMessage] = useState("");
  
  const location = useLocation();
  const navigate = useNavigate();
  
  const userId = location.state?.userId;
  const email = location.state?.email;

  useEffect(() => {
    // Redirect back to login if they bypassed it
    if (!userId) {
      navigate("/");
    }
  }, [userId, navigate]);

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const res = await api.post("/auth/verify-otp/", {
        user_id: userId,
        otp_code: code
      });

      const access = res.data?.access;
      const refresh = res.data?.refresh;
      const user = res.data?.user || {};

      if (access) localStorage.setItem("access_token", access);
      if (refresh) localStorage.setItem("refresh_token", refresh);
      if (res.data?.user) {
        localStorage.setItem("user", JSON.stringify(res.data.user));
      }

      // Determine redirect URL dynamically based on permissions sent from backend
      const redirectUrl = user?.default_redirect || "/dashboard";

      navigate(redirectUrl);
    } catch (err) {
      console.error("Verification failed:", err);
      setMessage(err.response?.data?.detail || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setMessage("");
    try {
      await api.post("/auth/resend-otp/", { user_id: userId });
      setMessage("A new verification code has been sent to your email.");
    } catch (err) {
      console.error("Resend failed:", err);
      setMessage("Failed to resend code. Please try again.");
    } finally {
      setResending(false);
    }
  };

  if (!userId) return null; // Prevent flicker before redirect

  return (
    <AuthLayout>
      <AuthCard>
        {/* Top Section */}
        <div className="flex flex-col items-center mt-4 md:mt-0">
          <Logo />
          <h2 className="text-xl font-bold text-white text-center mt-6">
            2-Step Verification
          </h2>
          <p className="text-sm text-gray-300 text-center mt-2 mb-2">
            We sent a verification code to <strong>{email}</strong>.
          </p>
        </div>

        {/* Middle Section (Grows to fill space) */}
        <div className="flex-grow flex flex-col justify-center py-6 gap-6">
          <form onSubmit={handleVerify} className="flex flex-col gap-6">
            <InputField
              id="code"
              label="Verification Code"
              placeholder="Enter 6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />

            {message && (
              <p className="text-sm text-center text-yellow-400">
                {message}
              </p>
            )}

            <div className="mt-2">
              <AuthButton
                type="submit"
                label="Verify Code"
                isLoading={loading}
                disabled={!code || code.length < 6}
              />
            </div>
          </form>

          <div className="flex justify-center mt-2">
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              {resending ? "Sending..." : "Didn't receive a code? Resend"}
            </button>
          </div>
        </div>

        {/* Bottom Spacer (Keep layout balanced) */}
        <div className="h-4"></div>
      </AuthCard>
    </AuthLayout>
  );
};

export default Mfa;