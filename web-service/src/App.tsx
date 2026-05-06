import { useGame } from "./contexts/GameContext";
import { Lobby } from "./pages/Lobby";
import { GameTable } from "./pages/GameTable";
import { Auth } from "./pages/Auth";

function App() {
  const { gameState, token } = useGame();

  if (!token) {
    return <Auth />;
  }

  // If we have game state, we are in a game
  if (gameState) {
    return <GameTable />;
  }

  // Otherwise we are in the lobby
  return <Lobby />;
}

export default App;
