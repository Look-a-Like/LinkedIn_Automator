import React from "react";
import SignUpHeader from "./SignUpHeader";
import SignUpMain from "./SignUpMain";
import SignUpFooter from "./SignUpFooter";


const SignUp = () => {
    return(
    <div className="flex flex-col min-h-screen bg-gradient-to-t overflow-y-hidden">
        <SignUpHeader/>
        <SignUpMain/>
        <SignUpFooter/>
    </div>
);
}

export default SignUp;