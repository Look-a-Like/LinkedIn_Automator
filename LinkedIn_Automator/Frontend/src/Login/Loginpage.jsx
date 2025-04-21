import React from "react";
import LoginHeader from "./LoginHeader";
import LoginMain from "./LoginMain";
import LoginFooter from "./LoginFooter";

function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-purple-100 to-blue-100">
      <LoginHeader />
      <LoginMain />
      <LoginFooter />
    </div>
  );
}

export default LoginPage;