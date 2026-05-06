import React, { useState } from "react";
import { useGame } from "../contexts/GameContext";

export const Auth: React.FC = () => {
  const { login } = useGame();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (isLogin) {
      try {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const res = await fetch("/api/token", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData.toString()
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Login failed");
        }

        const data = await res.json();
        login(data.access_token, data.username);
      } catch (err: any) {
        setError(err.message);
      }
    } else {
        try {
            const res = await fetch("/api/register", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ username, password })
            });
    
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Registration failed");
            }
            
            // Auto login after register
            setIsLogin(true);
            setError("Registration successful! Please log in.");
        } catch (err: any) {
            setError(err.message);
        }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">
      <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md border border-blue-500/30">
        <h1 className="text-4xl font-black mb-8 text-center bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent italic">
          EUCHRE.IO
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all"
              required
            />
          </div>

          {error && <div className={`text-sm p-3 rounded-lg border ${error.includes("successful") ? "text-green-400 bg-green-900/20 border-green-900/50" : "text-red-400 bg-red-900/20 border-red-900/50"}`}>{error}</div>}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg shadow-blue-900/20"
          >
            {isLogin ? "Log In" : "Register"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-400">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button onClick={() => setIsLogin(!isLogin)} className="text-blue-400 hover:underline font-bold">
                {isLogin ? "Register" : "Log In"}
            </button>
        </p>
      </div>
    </div>
  );
};