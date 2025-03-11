import React from 'react';

const SignUpHeader = () => {
    return (
        <div className='fixed top-8 left-0 right-0 mx-auto w-4/5 sm:w-3/4 h-20 sm:h-13 px-7 py-3 flex items-center z-20 bg-pink-200 rounded-full shadow-md'>
            <div className='font-bold text-xl mr-auto'>LOGO</div>
            <div className='flex justify-evenly flex-grow text-lg'>
                <span>header1</span>
                <span>header1</span>
                <span>header1</span>
                <span>header1</span>
                <span>header1</span>
            </div>
        </div>
    );
}

export default SignUpHeader;
