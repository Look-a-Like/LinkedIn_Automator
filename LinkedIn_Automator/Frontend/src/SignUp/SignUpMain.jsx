import React from 'react';
import SignUpContent from './SignUpContent';

const SignUpMain = () => {
    return(
        <div className="mt-20 p-10 flex flex-col lg:flex-row justify-center items-center">
            <div className="w-full lg:w-uto flex items-center justify-center">
                <SignUpContent/>
            </div>
        </div>    
    );
}

export default SignUpMain;
