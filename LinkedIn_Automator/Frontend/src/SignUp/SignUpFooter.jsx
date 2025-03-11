import React from "react";

const SignUpFooter = () => {
    return (
        <div className="bg-pink-200 py-8">
            <div className="max-w-7xl mx-auto px-8 flex justify-between items-center">
                <div className="text-4xl font-bold">LOGO</div>
                <div className="flex flex-col justify-center items-center space-y-4">
                    <div className="flex justify-center space-x-8">
                        <a href="#" className="text-black font-bold hover:text-gray-700">Support</a>
                        <a href="#" className="text-black font-bold hover:text-gray-700">FAQ</a>
                        <a href="#" className="text-black font-bold hover:text-gray-700">Terms</a>
                        <a href="#" className="text-black font-bold hover:text-gray-700">Privacy</a>
                    </div>
                    <div className="flex justify-center space-x-8">
                        <a href="#" className="text-black font-bold hover:text-gray-700">Careers</a>
                        <a href="#" className="text-black font-bold hover:text-gray-700">Latest Jobs</a>
                        <a href="#" className="text-black font-bold hover:text-gray-700">Latest Companies</a>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <span className="h-3 w-3 bg-black rounded-full"></span>
                    <span className="h-3 w-3 bg-black rounded-full"></span>
                    <span className="h-3 w-3 bg-black rounded-full"></span>
                </div>
            </div>
        </div>
    );
};

export default SignUpFooter;
