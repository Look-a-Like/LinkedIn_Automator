import React, { useState } from "react";
import { checkValidData } from "../utils/checkValidData";
import { Link, useNavigate } from "react-router-dom";
import { EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { account } from "../../appwrite";

const SignUpContent = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [visible, setVisible] = useState(false);
  const SignUpNavigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleOAuthLogin = async (provider) => {
    try {
      // Initiates OAuth login via Appwrite
      await account.createOAuth2Session(
        provider,
        "http://localhost:5173/MainPage",
        "http://localhost:5173/"
      );
    } catch (error) {
      console.error("OAuth login error", error);
      setErrorMessage("OAuth login failed. Please try again.");
    }
  };

  const handleFormSubmission = async () => {
    setIsSubmitting(true);
    const { email } = formData;
    const message = checkValidData(email);
    setErrorMessage(message);

    if (!message && formData.email && formData.password) {
      try {
        console.log("formData :: ", formData);
        const response = await fetch("", {
          method: "POST",
          headers: {
            token: "",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        });

        if (response.status === 200) {
          setFormData({
            username: "",
            email: "",
            password: "",
          });
          setErrorMessage("");
          SignUpNavigate("/");
        } else {
          console.error(
            "Incorrect combination of email and password",
            response.statusText
          );
        }
      } catch (error) {
        console.error("Error Logging in", error.message);
      } finally {
        setIsSubmitting(false);
      }
    } else {
      setIsSubmitting(false);
    }
  };

  const { username, email, password } = formData;
  const isActive = username && email && password && !isSubmitting;

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
            Join & Connect the Fastest Growing Online{" "}
            <span className="text-red-600">Community</span>
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
                className="px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border"
                placeholder="Enter your username ..."
                type="text"
                name="username"
                value={username}
                onChange={handleInputChange}
              />
            </div>
            <div className="py-2">
              <p className="text-lg lg:text-xl font-semibold ml-1">Email</p>
              <input
                className="px-4 py-2 my-1 w-full rounded-md outline-none text-lg lg:text-xl border"
                placeholder="Enter your email ..."
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
                {isSubmitting ? "Submitting..." : "Sign Up"}
              </button>
            </div>
          </form>
          <div className="text-center mt-4">
            <p>
              Own an Account?{" "}
              <Link to="/" className="text-red-600 font-semibold">
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
