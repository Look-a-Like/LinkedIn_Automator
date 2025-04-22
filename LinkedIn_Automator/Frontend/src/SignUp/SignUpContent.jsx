import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { account } from "../../appwrite";

const SignUpContent = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [visible, setVisible] = useState(false);
  const SignUpNavigate = useNavigate();

  // Email regex pattern
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // Validate form fields
  const validateField = (name, value) => {
    let error = "";

    switch (name) {
      case "email":
        if (!value) {
          error = "Email is required";
        } else if (!emailRegex.test(value)) {
          error = "Invalid email format";
        }
        break;
      case "password":
        if (!value) {
          error = "Password is required";
        } else if (value.length < 8) {
          error = "Password must be at least 8 characters";
        }
        break;
      case "username":
        if (!value) {
          error = "Username is required";
        } else if (value.length < 3) {
          error = "Username must be at least 3 characters";
        }
        break;
      default:
        break;
    }

    return error;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });

    // Validate field on change
    const error = validateField(name, value);
    setErrors({
      ...errors,
      [name]: error,
    });
  };

  const handleOAuthLogin = async (provider) => {
    try {
      // Initiates OAuth login via Appwrite
      await account.createOAuth2Session(provider, "http://localhost:5173/");
    } catch (error) {
      console.error("OAuth login error", error);
      setErrorMessage("OAuth login failed. Please try again.");
    }
  };

  const validateForm = () => {
    const newErrors = {
      username: validateField("username", formData.username),
      email: validateField("email", formData.email),
      password: validateField("password", formData.password),
    };

    setErrors(newErrors);

    // Return true if there are no errors
    return !Object.values(newErrors).some((error) => error);
  };

  const handleFormSubmission = async () => {
    // Validate all fields before submission
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      console.log("Submitting form data:", formData);

      // Modified to use FastAPI backend with fixed CORS settings
      const response = await fetch("http://localhost:8000/users/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          username: formData.username,
          password: formData.password,
        }),
        credentials: "include", // Include credentials
        mode: "cors", // Explicitly set CORS mode
      });

      // Log response status
      console.log("Response status:", response.status);

      if (response.ok) {
        // If registration is successful, proceed to login
        const userData = await response.json();
        console.log("Registration successful:", userData);

        // Login with the newly created account
        await loginUser(formData.email, formData.password);
      } else {
        // Handle registration errors
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Registration failed" }));
        setErrorMessage(
          errorData.detail || "Registration failed. Please try again."
        );
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error("Error during registration:", error);
      setErrorMessage("Connection error. Please try again.");
      setIsSubmitting(false);
    }
  };

  // Login function to be called after successful registration
  const loginUser = async (email, password) => {
    try {
      const response = await fetch("http://localhost:8000/users/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors", // Explicitly set CORS mode
        credentials: "include", // Include credentials
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Login successful:", data);

        // Store token and user info
        localStorage.setItem("accessToken", data.access_token);
        localStorage.setItem(
          "userInfo",
          JSON.stringify({
            id: data.user.id,
            email: data.user.email,
            username: data.user.username,
          })
        );

        // Reset form
        setFormData({
          username: "",
          email: "",
          password: "",
        });

        // Navigate to dashboard directly instead of login page
        SignUpNavigate("/");
      } else {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Login failed" }));
        setErrorMessage(
          errorData.detail ||
            "Registration successful but login failed. Please login manually."
        );
        setIsSubmitting(false);

        // Navigate to login page if registration was successful but login failed
        setTimeout(() => SignUpNavigate("/"), 2000);
      }
    } catch (error) {
      console.error("Error during login:", error);
      setErrorMessage(
        "Registration successful but login failed. Please login manually."
      );
      setIsSubmitting(false);

      // Navigate to login page
      setTimeout(() => SignUpNavigate("/"), 2000);
    }
  };

  const { username, email, password } = formData;

  // Form is active only if all fields have values, no errors exist, and not in submitting state
  const isActive =
    username &&
    email &&
    password &&
    !errors.username &&
    !errors.email &&
    !errors.password &&
    !isSubmitting;

  return (
    <div className="flex h-screen">
      {/* Left side content */}
      <div className="w-1/2 flex flex-col justify-center items-center bg-white p-8 lg:p-12">
        <div className="mb-8">
          {/* Placeholder for 3D image with animations */}
          <div className="w-64 h-64 bg-gray-300 flex items-center justify-center">
            <span className="text-center text-gray-500">
              NEED TO KEEP A 3D IMAGE WITH SOME ANIMATIONS AS A VIDEO SHOULD BE
              PLACE...
            </span>
          </div>
        </div>
        <div className="text-center">
          <h1 className="text-3xl lg:text-4xl font-bold mb-4">
            Software For
            <br></br>
            <span className="text-blue-500">Job Automation</span>
          </h1>
          <p className="text-gray-500">Description part</p>
        </div>
      </div>
      {/* Right side form */}
      <div className="w-1/2 flex justify-center items-center p-8 lg:p-12">
        <div className="max-w-md w-full">
          <div className="w-full py-4 lg:py-6 font-semibold text-center text-xl lg:text-2xl">
            Join & Connect the Fastest Growing Online{" "}
            <span className="text-blue-600">Community</span>
          </div>
          <div className="flex justify-center mt-4 mb-6">
            <button
              onClick={() => handleOAuthLogin("google")}
              className="mx-2 px-4 py-2 bg-white border border-gray-300 rounded-full flex items-center"
            >
              <img
                src="path/to/google-icon.png"
                alt="Google"
                className="w-5 h-5 mr-2"
              />{" "}
              Sign up with Google
            </button>
            <button className="mx-2 px-4 py-2 bg-white border border-gray-300 rounded-full flex items-center">
              <img
                src="path/to/github-icon.png"
                alt="Github"
                className="w-5 h-5 mr-2"
              />{" "}
              Sign up with Github
            </button>
          </div>
          <form
            onSubmit={(e) => e.preventDefault()}
            className="px-6 lg:px-8 mt-4"
          >
            <div className="py-2">
              <p className="text-lg lg:text-xl font-semibold ml-1">Username</p>
              <input
                className={`px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border ${
                  errors.username ? "border-red-500" : ""
                }`}
                placeholder="Enter your username ..."
                type="text"
                name="username"
                value={username}
                onChange={handleInputChange}
                disabled={isSubmitting}
              />
              {errors.username && (
                <p className="text-red-500 text-sm mt-1">{errors.username}</p>
              )}
            </div>
            <div className="py-2">
              <p className="text-lg lg:text-xl font-semibold ml-1">Email</p>
              <input
                className={`px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border ${
                  errors.email ? "border-red-500" : ""
                }`}
                placeholder="Enter your email ..."
                type="email"
                name="email"
                value={email}
                onChange={handleInputChange}
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className="text-red-500 text-sm mt-1">{errors.email}</p>
              )}
            </div>
            <div className="py-2 relative">
              <p className="text-lg lg:text-xl font-semibold ml-1">Password</p>
              <div className="relative">
                <input
                  className={`px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border pr-10 ${
                    errors.password ? "border-red-500" : ""
                  }`}
                  placeholder="Enter your password ..."
                  type={visible ? "text" : "password"}
                  name="password"
                  value={password}
                  onChange={handleInputChange}
                  disabled={isSubmitting}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 cursor-pointer text-xl">
                  {visible ? (
                    <EyeOutlined onClick={() => setVisible(!visible)} />
                  ) : (
                    <EyeInvisibleOutlined
                      onClick={() => setVisible(!visible)}
                    />
                  )}
                </div>
              </div>
              {errors.password && (
                <p className="text-red-500 text-sm mt-1">{errors.password}</p>
              )}
            </div>

            {errorMessage && (
              <p className="text-rose-500 mt-2 text-center">{errorMessage}</p>
            )}

            <div className="flex items-center mt-4">
              <input
                type="checkbox"
                id="rememberMe"
                className="mr-2"
                disabled={isSubmitting}
              />
              <label htmlFor="rememberMe" className="text-lg lg:text-xl">
                Remember me
              </label>
            </div>

            <div className="mt-6 lg:mt-10 flex justify-center">
              {isSubmitting ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                  <p className="text-gray-600">Creating your account...</p>
                </div>
              ) : (
                <button
                  disabled={!isActive}
                  className={`px-6 py-2 m-2 ${
                    isActive ? "hover:bg-blue-600" : "opacity-50"
                  } text-lg lg:text-xl rounded-full font-semibold bg-blue-500 text-white transition duration-300`}
                  onClick={handleFormSubmission}
                >
                  Sign Up
                </button>
              )}
            </div>
          </form>
          <div className="text-center mt-4">
            <p>
              Own an Account?{" "}
              <Link
                to="/"
                className="text-blue-600 font-semibold hover:underline"
              >
                JUMP RIGHT IN
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignUpContent;
