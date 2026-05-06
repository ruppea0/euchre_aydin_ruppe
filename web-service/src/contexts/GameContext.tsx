import React, { createContext, useContext, useState, useCallback, useRef } from "react";
import type { GameStateUpdate, LobbyUpdate, Action } from "../types/game";

export interface LobbySettings {
  winThreshold: number;
  screwTheDealer: boolean;
  noTrumpEnabled: boolean;
  bottom3Enabled: boolean;
}

interface GameContextType {
  token: string | null;
  playerName: string | null;
  lobbyId: string | null;
  gameState: GameStateUpdate | null;
  lobbyUpdate: LobbyUpdate | null;
  error: string | null;
  isConnected: boolean;
  login: (token: string, username: string) => void;
  logout: () => void;
  joinLobby: (lobbyId: string, settings?: LobbySettings) => void;
  sendAction: (action: Action) => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const GameProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [playerName, setPlayerName] = useState<string | null>(localStorage.getItem("username"));
  const [lobbyId, setLobbyId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameStateUpdate | null>(null);
  const [lobbyUpdate, setLobbyUpdate] = useState<LobbyUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);

  const login = (newToken: string, username: string) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("username", username);
    setToken(newToken);
    setPlayerName(username);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setToken(null);
    setPlayerName(null);
    setLobbyId(null);
    setGameState(null);
    setLobbyUpdate(null);
    if (socketRef.current) {
        socketRef.current.close();
    }
  };

  const connect = useCallback((lid: string, settings?: LobbySettings) => {
    if (!token) return;
    
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let wsUrl = `${protocol}//${window.location.host}/ws/${lid}?token=${token}`;
    if (settings) {
      wsUrl += `&win_threshold=${settings.winThreshold}`;
      wsUrl += `&screw_the_dealer=${settings.screwTheDealer}`;
      wsUrl += `&no_trump_enabled=${settings.noTrumpEnabled}`;
      wsUrl += `&bottom_3_enabled=${settings.bottom3Enabled}`;
    }
    
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "lobby_update") {
        setLobbyUpdate(data);
      } else if (data.type === "game_state") {
        setGameState(data);
      } else if (data.type === "error") {
        setError(data.message);
        setTimeout(() => {
          setError(prev => prev === data.message ? null : prev);
        }, 5000);
      }
    };

    socket.onclose = (event) => {
      setIsConnected(false);
      setLobbyId(null);
      if (event.code === 1008) {
          logout(); // Invalid token
      }
    };

    socket.onerror = () => {
      setError("WebSocket error occurred.");
    };

    socketRef.current = socket;
  }, [token]);

  const joinLobby = (lid: string, settings?: LobbySettings) => {
    setLobbyId(lid);
    connect(lid, settings);
  };

  const sendAction = (action: Action) => {
    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify(action));
    }
  };

  return (
    <GameContext.Provider
      value={{
        token,
        playerName,
        lobbyId,
        gameState,
        lobbyUpdate,
        error,
        login,
        logout,
        joinLobby,
        sendAction,
        isConnected,
      }}
    >
      {children}
    </GameContext.Provider>
  );
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error("useGame must be used within a GameProvider");
  }
  return context;
};
