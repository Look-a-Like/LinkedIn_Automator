import React from 'react';
import LoginForm from './LoginForm';

const LoginMain = () => {
    return(
        <div className="mt-20 p-10 flex flex-col lg:flex-row justify-center items-center">
            <div className="w-full lg:w-uto flex items-center justify-center">
                <LoginForm/>
            </div>
        </div>    
    );
}

export default LoginMain;
