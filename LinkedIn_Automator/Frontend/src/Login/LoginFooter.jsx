import React from "react";

const LoginFooter = () => {
  return (
    <footer className="bg-white py-4 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 flex flex-col items-center text-sm text-gray-600">
        <div className="flex space-x-4 mb-2">
          <a href="#" className="hover:text-purple-600">Support</a>
          <a href="#" className="hover:text-purple-600">Terms</a>
          <a href="#" className="hover:text-purple-600">Privacy</a>
        </div>
        <div className="flex space-x-4">
          <a href="https://twitter.com" className="hover:text-purple-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z" />
            </svg>
          </a>
          <a href="https://linkedin.com" className="hover:text-purple-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 3a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14m-.5 15.5v-5.3a3.26 3.26 0 00-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 011.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 001.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 00-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
            </svg>
          </a>
        </div>
        <p className="mt-2">© 2025 JobApplier. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default LoginFooter;