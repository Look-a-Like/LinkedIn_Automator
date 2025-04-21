import React, { useState } from "react";
import { checkValidData } from "../utils/checkValidData";
import { Link, useNavigate } from "react-router-dom";
import { EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { account } from "../../appwrite";
import jobSearchImage from "./image.png"; // Assuming image.png is in src/Login/

const LoginForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [visible, setVisible] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleOAuthLogin = async (provider) => {
    try {
      await account.createOAuth2Session(
        provider,
        "http://localhost:8501",
        "http://localhost:5173/"
      );
    } catch (error) {
      console.error("OAuth login error", error);
      setErrorMessage("OAuth login failed. Please try again.");
    }
  };

  const handleFormSubmission = async () => {
    setIsSubmitting(true);
    const { email, password } = formData;
    const message = checkValidData(email);
    setErrorMessage(message);

    if (!message && email && password) {
      try {
        console.log("Attempting login with:", { email, password });

        const response = await fetch("http://localhost:8000/users/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          mode: "cors",
          credentials: "include",
          body: JSON.stringify({
            email: email,
            password: password,
          }),
        });

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Login failed" }));
          console.error("Login failed:", errorData);
          setErrorMessage(
            errorData.detail ||
              "Login failed. Please check your credentials and try again."
          );
          setIsSubmitting(false);
          return;
        }

        const result = await response.json();
        console.log("Login successful:", result);

        localStorage.setItem("userEmail", email);
        localStorage.setItem("userId", result.user.id);
        localStorage.setItem("username", result.user.username);
        localStorage.setItem("token", result.access_token);

        setFormData({
          email: "",
          password: "",
        });
        setErrorMessage("");

        await fetch("http://localhost:8000/proxy/fivetran", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            event: "user_login",
            user_id: result.user.id,
          }),
        });

        window.location.href = `http://localhost:8501?user_id=${result.user.id}`;
      } catch (error) {
        console.error("Error during login API call:", error);
        setErrorMessage(
          "Connection error. Please check your internet connection and try again."
        );
        setIsSubmitting(false);
      }
    } else {
      setIsSubmitting(false);
    }
  };

  const { email, password } = formData;
  const isActive = email && password && !isSubmitting;

  return (
    <div className="flex h-screen bg-gradient-to-br from-purple-100 to-blue-100">
      <div className="w-1/2 flex flex-col justify-center items-center p-8">
        <div className="w-80 h-96 bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
          <img src={jobSearchImage} alt="Job Search Illustration" className="w-full h-full object-cover" />
        </div>
      </div>
      <div className="w-1/2 flex justify-center items-center p-8">
        <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-md border border-gray-200">
          <h2 className="text-lg font-semibold text-center text-gray-800 mb-4">Welcome Back</h2>
          <h3 className="text-sm text-center text-gray-600 mb-4">Sign In With</h3>
          <div className="flex justify-center gap-4 mb-4">
            <button
              onClick={() => handleOAuthLogin("google")}
              className="px-4 py-2 bg-white border border-gray-300 rounded-full flex items-center hover:bg-gray-50 transition-colors"
            >
              <img
                src="https://www.google.com/favicon.ico"
                alt="Google"
                className="w-5 h-5 mr-2"
              />{" "}
              Google
            </button>
            <button
              onClick={() => handleOAuthLogin("github")}
              className="px-4 py-2 bg-white border border-gray-300 rounded-full flex items-center hover:bg-gray-50 transition-colors"
            >
              <img
                src="https://github.com/favicon.ico"
                alt="Github"
                className="w-5 h-5 mr-2"
              />{" "}
              Github
            </button>
          </div>
          <div className="text-center text-gray-500 mb-4">or</div>
          <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email or Username</label>
              <input
                className="w-full px-3 py-2 mt-1 rounded-md border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Enter email or username..."
                type="text"
                name="email"
                value={email}
                onChange={handleInputChange}
                disabled={isSubmitting}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <div className="relative">
                <input
                  className="w-full px-3 py-2 mt-1 rounded-md border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 pr-10"
                  placeholder="Enter password..."
                  type={visible ? "text" : "password"}
                  name="password"
                  value={password}
                  onChange={handleInputChange}
                  disabled={isSubmitting}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-500">
                  {visible ? (
                    <EyeOutlined onClick={() => setVisible(!visible)} />
                  ) : (
                    <EyeInvisibleOutlined onClick={() => setVisible(!visible)} />
                  )}
                </div>
              </div>
            </div>
            {errorMessage && <p className="text-red-500 text-sm">{errorMessage}</p>}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input type="checkbox" id="rememberMe" className="mr-2 h-4 w-4" />
                <label htmlFor="rememberMe" className="text-sm text-gray-700">Remember me</label>
              </div>
              <Link to="/forgot-password" className="text-sm text-purple-600 hover:underline">
                Forgot Password?
              </Link>
            </div>
            <div className="text-center">
              {isSubmitting ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mb-2"></div>
                  <p className="text-gray-600 text-sm">Logging in...</p>
                </div>
              ) : (
                <button
                  disabled={!isActive}
                  className={`w-full px-4 py-2 rounded-md font-medium text-white ${isActive ? "bg-purple-600 hover:bg-purple-700" : "bg-gray-300"} transition-colors`}
                  onClick={handleFormSubmission}
                >
                  Log In
                </button>
              )}
            </div>
          </form>
          <p className="text-center text-sm text-gray-600 mt-4">
            Don’t have an account?{" "}
            <Link to="/SignUp" className="text-purple-600 font-medium hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;