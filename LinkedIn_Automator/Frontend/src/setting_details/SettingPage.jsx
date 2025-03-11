import React from 'react';
import NavBar from './NavBar';
import SettingContent from './SettingContent';

const Settings = () => {
    return (
        <div className="flex h-screen overflow-hidden">
            <NavBar />
            <div className="flex-grow p-8 bg-pink-100 overflow-y-auto">
                <SettingContent/>
            </div>
        </div>
    );
};

export default Settings;
