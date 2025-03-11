import React from 'react';
import LoginHeader from './LoginHeader';
import LoginMain from './LoginMain';
import LoginFooter from './LoginFooter';

function LoginPage() {
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-t overflow-y-hidden">
      <LoginHeader/>
      <LoginMain/>
      <LoginFooter/>
    </div>
  );
}

export default LoginPage;