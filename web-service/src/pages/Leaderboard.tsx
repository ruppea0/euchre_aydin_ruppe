import React, { useEffect, useState } from "react";
import { Trophy, RefreshCw } from "lucide-react";

interface LeaderboardEntry {
  username: string;
  games_played: number;
  games_won: number;
  win_percentage: number;
}

export const Leaderboard: React.FC = () => {
  const [data, setData] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchLeaderboard = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/leaderboard");
      if (!res.ok) {
        throw new Error("Failed to fetch leaderboard data");
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  return (
    <div className="bg-gray-800 p-8 rounded-xl shadow-2xl w-full max-w-4xl border border-yellow-500/30 mx-auto mt-8">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-3xl font-black text-yellow-400 flex items-center gap-3">
          <Trophy className="w-8 h-8" /> Hall of Fame
        </h2>
        <button
          onClick={fetchLeaderboard}
          className="bg-gray-700 hover:bg-gray-600 text-white p-2 rounded-lg transition-colors border border-gray-600"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {error ? (
        <div className="bg-red-900/50 border border-red-500/50 text-red-200 p-4 rounded-lg">
          {error}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b-2 border-gray-700 text-gray-400 text-sm uppercase tracking-wider">
                <th className="p-4 font-semibold">Rank</th>
                <th className="p-4 font-semibold">Player</th>
                <th className="p-4 font-semibold text-center">Played</th>
                <th className="p-4 font-semibold text-center">Won</th>
                <th className="p-4 font-semibold text-right">Win Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading && data.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    Loading champions...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500 italic">
                    No matches played yet.
                  </td>
                </tr>
              ) : (
                data.map((user, idx) => (
                  <tr
                    key={user.username}
                    className="hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="p-4 font-bold text-gray-300">
                      {idx === 0 ? (
                        <span className="text-yellow-400 flex items-center gap-1">
                          <Trophy className="w-4 h-4" /> 1
                        </span>
                      ) : idx === 1 ? (
                        <span className="text-gray-300">2</span>
                      ) : idx === 2 ? (
                        <span className="text-amber-600">3</span>
                      ) : (
                        <span className="text-gray-500">{idx + 1}</span>
                      )}
                    </td>
                    <td className="p-4 font-bold text-white">{user.username}</td>
                    <td className="p-4 text-center text-gray-400">{user.games_played}</td>
                    <td className="p-4 text-center text-green-400 font-semibold">
                      {user.games_won}
                    </td>
                    <td className="p-4 text-right font-mono">
                      <span
                        className={`px-2 py-1 rounded ${
                          user.win_percentage >= 50
                            ? "bg-green-900/30 text-green-400"
                            : "bg-red-900/30 text-red-400"
                        }`}
                      >
                        {user.win_percentage.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
