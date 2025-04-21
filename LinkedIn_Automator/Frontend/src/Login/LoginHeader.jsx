import React, { useState } from "react";
import { Link } from "react-router-dom";

const LoginHeader = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-purple-800 text-white py-3 shadow-md">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
        <Link to="/" className="text-2xl font-semibold">
          JobApplier
        </Link>
        <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
          <a href="#" className="hover:text-purple-200 transition-colors">Home</a>
          <a href="#" className="hover:text-purple-200 transition-colors">Jobs</a>
          <a href="#" className="hover:text-purple-200 transition-colors">Profile</a>
          <a href="#" className="hover:text-purple-200 transition-colors">About</a>
          <Link
            to="/SignUp"
            className="bg-purple-600 px-4 py-2 rounded hover:bg-purple-700 transition-colors"
          >
            Sign Up
          </Link>
        </nav>
        <button
          className="md:hidden text-white"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16m-7 6h7"}
            />
          </svg>
        </button>
      </div>
      {isMenuOpen && (
        <nav className="md:hidden bg-purple-800 p-4">
          <div className="flex flex-col items-center space-y-2 text-sm font-medium text-white">
            <a href="#" className="hover:text-purple-200 transition-colors">Home</a>
            <a href="#" className="hover:text-purple-200 transition-colors">Jobs</a>
            <a href="#" className="hover:text-purple-200 transition-colors">Profile</a>
            <a href="#" className="hover:text-purple-200 transition-colors">About</a>
            <Link
              to="/SignUp"
              className="bg-purple-600 px-4 py-2 rounded hover:bg-purple-700 transition-colors"
            >
              Sign Up
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
};

export default LoginHeader;