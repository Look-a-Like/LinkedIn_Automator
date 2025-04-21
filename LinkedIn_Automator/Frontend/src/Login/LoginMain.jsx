import React from "react";
import LoginForm from "./LoginForm";

const LoginMain = () => {
  return (
    <main className="flex items-center justify-center flex-1 p-4 bg-gradient-to-br from-purple-100 to-blue-100">
      <LoginForm />
    </main>
  );
};

export default LoginMain;