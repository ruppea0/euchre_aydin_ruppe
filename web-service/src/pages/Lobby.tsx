import React, { useState } from "react";
import { useGame } from "../contexts/GameContext";
import { Users, Play, Plus, LogOut, Trophy } from "lucide-react";
import { Leaderboard } from "./Leaderboard";

export const Lobby: React.FC = () => {
  const { joinLobby, lobbyUpdate, isConnected, playerName, error, logout } = useGame();
  const [lobbyInput, setLobbyInput] = useState("");
  const [activeTab, setActiveTab] = useState<"play" | "leaderboard">("play");

  // Lobby Settings
  const [winThreshold, setWinThreshold] = useState(10);
  const [screwTheDealer, setScrewTheDealer] = useState(true);
  const [noTrumpEnabled, setNoTrumpEnabled] = useState(true);
  const [bottom3Enabled, setBottom3Enabled] = useState(true);

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    if (lobbyInput) {
      joinLobby(lobbyInput, {
        winThreshold,
        screwTheDealer,
        noTrumpEnabled,
        bottom3Enabled
      });
    }
  };

  const handleAddBot = async () => {
    if (!lobbyUpdate?.lobby_id) return;
    try {
      await fetch(`/api/lobbies/${lobbyUpdate.lobby_id}/add-bot`, {
        method: 'POST',
      });
    } catch (err) {
      console.error("Failed to add bot", err);
    }
  };

  if (isConnected && lobbyUpdate) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4 relative">
        <button onClick={logout} className="absolute top-4 right-4 flex items-center gap-2 text-gray-400 hover:text-white transition-colors bg-gray-800 px-4 py-2 rounded-full shadow-lg border border-white/5 hover:border-red-500/50">
           <LogOut className="w-4 h-4"/> Logout
        </button>

        <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md border border-blue-500/30 mt-12">
          <h1 className="text-3xl font-bold mb-6 text-center text-blue-400 flex items-center justify-center gap-2">
            <Users className="w-8 h-8" /> Lobby: {lobbyUpdate.lobby_id}
          </h1>
          
          <div className="space-y-4 mb-8">
            <h2 className="text-xl font-semibold border-b border-gray-700 pb-2">Players ({lobbyUpdate.players.length}/4)</h2>
            <ul className="space-y-2">
              {lobbyUpdate.players.map((p, i) => (
                <li key={i} className="bg-gray-700/50 p-3 rounded-lg flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-bold">
                    {p[0].toUpperCase()}
                  </div>
                  <span>{p}</span>
                  {p === playerName && <span className="text-xs bg-blue-600 px-2 py-0.5 rounded-full ml-auto">You</span>}
                </li>
              ))}
              {[...Array(4 - lobbyUpdate.players.length)].map((_, i) => (
                <li key={i + 10} className="bg-gray-700/20 p-3 rounded-lg border border-dashed border-gray-600 text-gray-500 italic">
                  Waiting for player...
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center justify-center gap-3 text-sm text-gray-400 animate-pulse">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Waiting for {4 - lobbyUpdate.players.length} more players to start
            </div>
            
            {lobbyUpdate.players.length < 4 && (
              <button 
                onClick={handleAddBot}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg shadow-indigo-900/20 text-sm"
              >
                <Plus className="w-4 h-4" /> Add Bot
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4 relative">
      <button onClick={logout} className="absolute top-4 right-4 flex items-center gap-2 text-gray-400 hover:text-white transition-colors bg-gray-800 px-4 py-2 rounded-full shadow-lg border border-white/5 hover:border-red-500/50">
          <LogOut className="w-4 h-4"/> Logout
      </button>

      <div className="w-full max-w-4xl flex justify-center mb-8 space-x-4">
        <button
          onClick={() => setActiveTab("play")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
            activeTab === "play"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-900/30 scale-105"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
          }`}
        >
          <Play className="w-5 h-5" /> Play Game
        </button>
        <button
          onClick={() => setActiveTab("leaderboard")}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
            activeTab === "leaderboard"
              ? "bg-yellow-600 text-white shadow-lg shadow-yellow-900/30 scale-105"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
          }`}
        >
          <Trophy className="w-5 h-5" /> Leaderboard
        </button>
      </div>

      {activeTab === "play" ? (
        <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-md border border-blue-500/30">
          <h1 className="text-4xl font-black mb-8 text-center bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent italic">
            EUCHRE.IO
          </h1>

          <div className="text-center mb-6">
              <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">Logged in as</p>
              <p className="text-xl font-black text-white">{playerName}</p>
          </div>

          <form onSubmit={handleJoin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1 text-center">Lobby ID</label>
              <input
                type="text"
                value={lobbyInput}
                onChange={(e) => setLobbyInput(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all text-center uppercase tracking-widest font-black"
                placeholder="e.g. ROOM-1"
                required
              />
            </div>

            {/* Game Settings Section */}
            <div className="bg-gray-900/50 p-4 rounded-xl border border-white/5 space-y-4">
               <h3 className="text-[10px] uppercase font-black text-gray-500 tracking-widest mb-2 text-center">House Rules</h3>
               
               <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-gray-300">Screw The Dealer</label>
                  <button 
                    type="button"
                    onClick={() => setScrewTheDealer(!screwTheDealer)}
                    className={`w-12 h-6 rounded-full transition-colors relative ${screwTheDealer ? 'bg-blue-600' : 'bg-gray-600'}`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${screwTheDealer ? 'left-7' : 'left-1'}`}></div>
                  </button>
               </div>

               <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-gray-300">No Trump Rule</label>
                  <button 
                    type="button"
                    onClick={() => setNoTrumpEnabled(!noTrumpEnabled)}
                    className={`w-12 h-6 rounded-full transition-colors relative ${noTrumpEnabled ? 'bg-blue-600' : 'bg-gray-600'}`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${noTrumpEnabled ? 'left-7' : 'left-1'}`}></div>
                  </button>
               </div>

               <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-gray-300">Bottom 3 Rule</label>
                  <button 
                    type="button"
                    onClick={() => setBottom3Enabled(!bottom3Enabled)}
                    className={`w-12 h-6 rounded-full transition-colors relative ${bottom3Enabled ? 'bg-blue-600' : 'bg-gray-600'}`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${bottom3Enabled ? 'left-7' : 'left-1'}`}></div>
                  </button>
               </div>

               <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-gray-300">Win Points</label>
                  <select 
                    value={winThreshold}
                    onChange={(e) => setWinThreshold(Number(e.target.value))}
                    className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm font-bold focus:outline-none text-white"
                  >
                    <option value={1}>1</option>
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={21}>21</option>
                  </select>
               </div>
            </div>

            {error && <div className="text-red-400 text-sm bg-red-900/20 p-3 rounded-lg border border-red-900/50">{error}</div>}

            <div className="flex gap-4 pt-2">
              <button
                type="submit"
                className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-black uppercase tracking-widest py-4 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-xl shadow-indigo-900/20 hover:scale-105 active:scale-95"
              >
                <Play className="w-5 h-5 fill-current" /> Join Room
              </button>
            </div>
          </form>
        </div>
      ) : (
        <Leaderboard />
      )}
    </div>
  );
};
