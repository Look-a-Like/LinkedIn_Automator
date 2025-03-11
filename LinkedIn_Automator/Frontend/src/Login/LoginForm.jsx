import React, { useState } from "react";
import { checkValidData } from "../utils/checkValidData";
import { Link, useNavigate } from "react-router-dom";
import { EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { account } from "../../appwrite";

const LoginForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [visible, setVisible] = useState(false);
  const LoginNavigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // Function to handle OAuth login
  const handleOAuthLogin = async (provider) => {
    try {
      // Initiates OAuth login via Appwrite
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

  const handleFormSubmission = () => {
    const { email } = formData;
    const message = checkValidData(email);
    setErrorMessage(message);

    if (!message && formData.email) {
      // Store the user email address
      localStorage.setItem("userEmail", formData.email);
      setFormData({
        email: "",
        password: "",
      });
      setErrorMessage("");
      window.location.href = "http://localhost:8501";
    } else {
      setIsSubmitting(false);
    }
  };

  // const handleFormSubmission = async () => {
  //     setIsSubmitting(true);
  //     const { email } = formData;
  //     const message = checkValidData(email);
  //     setErrorMessage(message);

  //     if (!message && formData.email && formData.password) {
  //         try {
  //             console.log("formData :: ", formData);
  //             const response = await fetch('YOUR_API_ENDPOINT', {
  //                 method: 'POST',
  //                 headers: {
  //                     'token': "YOUR_TOKEN",
  //                     'Content-Type': 'application/json',
  //                 },
  //                 body: JSON.stringify(formData),
  //             });

  //             const result = await response.json();

  //             if (response.ok && result.data) {
  //                 // Store the user's email address in localStorage
  //                 localStorage.setItem('userEmail', formData.email);

  //                 // Navigate to the main page
  //                 setFormData({
  //                     email: '',
  //                     password: '',
  //                 });
  //                 setErrorMessage('');
  //                 LoginNavigate('/MainPage');
  //             } else {
  //                 // Handle case where response is not ok or data is missing
  //                 setErrorMessage('Login failed. Please check your credentials and try again.');
  //             }
  //         } catch (error) {
  //             console.error('Error Logging in', error.message);
  //             setErrorMessage('An error occurred while logging in. Please try again later.');
  //         } finally {
  //             setIsSubmitting(false);
  //         }
  //     } else {
  //         setIsSubmitting(false);
  //     }
  // };

  const { email, password } = formData;
  const isActive = email && password && !isSubmitting;

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
            <span className="text-red-500">Job Automation</span>
          </h1>
          <p className="text-gray-500">Description part</p>
        </div>
      </div>
      {/* Right side form */}
      <div className="w-1/2 flex justify-center items-center p-8 lg:p-12">
        <div className="max-w-md w-full">
          <div className="w-full py-4 lg:py-6 font-semibold text-center text-xl lg:text-2xl">
            Welcome back to <span className="text-red-600">Job Automator </span>{" "}
            Community
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
              Log In with Google
            </button>
            <button className="mx-2 px-4 py-2 bg-white border border-gray-300 rounded-full flex items-center">
              <img
                src="path/to/github-icon.png"
                alt="Github"
                className="w-5 h-5 mr-2"
              />{" "}
              Log In with Github
            </button>
          </div>
          <form
            onSubmit={(e) => e.preventDefault()}
            className="px-6 lg:px-8 mt-4"
          >
            <div className="py-2">
              <p className="text-lg lg:text-xl font-semibold ml-1">
                Email or Username
              </p>
              <input
                className="px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border"
                placeholder="Enter your email or username ..."
                type="text"
                name="email"
                value={email}
                onChange={handleInputChange}
              />
            </div>
            <div className="py-2 relative">
              <p className="text-lg lg:text-xl font-semibold ml-1">Password</p>
              <div className="relative">
                <input
                  className="px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border pr-10"
                  placeholder="Enter your password ..."
                  type={visible ? "text" : "password"}
                  name="password"
                  value={password}
                  onChange={handleInputChange}
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
            </div>
            {errorMessage && <p className="text-rose-500">{errorMessage}</p>}
            <div className="flex items-center mt-4">
              <input type="checkbox" id="rememberMe" className="mr-2" />
              <label htmlFor="rememberMe" className="text-lg lg:text-xl">
                Remember me
              </label>
            </div>
            <div className="mt-6 lg:mt-10 flex justify-center">
              <button
                disabled={!isActive}
                className={`px-6 py-2 m-2 ${
                  isActive ? "" : "opacity-50"
                } text-lg lg:text-xl rounded-full font-semibold bg-red-500 text-white`}
                onClick={handleFormSubmission}
              >
                {isSubmitting ? "Submitting..." : "LOG IN"}
              </button>
            </div>
          </form>
          <div className="text-center mt-4">
            <p>
              No Account yet?{" "}
              <Link to="/SignUp" className="text-red-600 font-semibold">
                SIGN UP
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
