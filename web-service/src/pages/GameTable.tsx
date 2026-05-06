import React from "react";
import { useGame } from "../contexts/GameContext";
import { Suits, type Suit, type Card as CardType } from "../types/game";
import { Plus } from "lucide-react";

export const GameTable: React.FC = () => {
  const { gameState, playerName, sendAction, error } = useGame();
  const [selectingBottom3, setSelectingBottom3] = React.useState<CardType[]>([]);
  const [isSelectingBottom3, setIsSelectingBottom3] = React.useState(false);

  if (!gameState || !playerName) return null;

  React.useEffect(() => {
    if (gameState.current_bidder !== gameState.my_seat_id || gameState.bidding_phase === 3) {
        setIsSelectingBottom3(false);
        setSelectingBottom3([]);
    }
  }, [gameState.current_bidder, gameState.my_seat_id, gameState.bidding_phase]);

  const handleCardClick = (card: CardType) => {
    // If selecting for Bottom 3
    if (selectingBottom3.length > 0 || (gameState.bottom_3_enabled && !gameState.bottom_3_used && gameState.bidding_phase === 1 && gameState.current_bidder === gameState.my_seat_id)) {
        // Only allow selecting 9s and 10s
        if (card.rank === 9 || card.rank === 10 || card.rank === "NINE" || card.rank === "TEN") {
            setSelectingBottom3(prev => {
                const alreadySelected = prev.find(c => c.suit === card.suit && c.rank === card.rank);
                if (alreadySelected) {
                    return prev.filter(c => c.suit !== card.suit || c.rank !== card.rank);
                }
                if (prev.length < 3) {
                    return [...prev, card];
                }
                return prev;
            });
            return;
        }
    }

    if (gameState.bidding_phase === 3 && gameState.my_seat_id === gameState.dealer_id) {
        sendAction({
            type: "dealer_discard",
            suit: card.suit,
            rank: String(card.rank),
        });
    } else {
        sendAction({
            type: "play_card",
            suit: card.suit,
            rank: String(card.rank),
        });
    }
  };

  const handleBid = (suit: Suit | null, alone: boolean = false) => {
    sendAction({ type: "call_trump", suit, alone });
  };

  const handleReturnToLobby = () => {
    window.location.href = "/lobby";
  };

  const handleBottom3Confirm = () => {
    if (selectingBottom3.length === 3) {
        sendAction({
            type: "bottom_3",
            cards: selectingBottom3,
        });
        setSelectingBottom3([]);
        setIsSelectingBottom3(false);
    }
  };

  const isAlphaTeam = gameState.my_seat_id % 2 === 0;
  const alphaScore = gameState.team_scores[0];
  const bravoScore = gameState.team_scores[1];
  const alphaWins = alphaScore >= gameState.win_threshold;
  const bravoWins = bravoScore >= gameState.win_threshold;
  const myTeamWins = (isAlphaTeam && alphaWins) || (!isAlphaTeam && bravoWins);

  const getRelativeSeat = (id: number) => (id - gameState.my_seat_id + 4) % 4;

  // Helper to render a card
  const renderCard = (card: CardType, onClick?: () => void, disabled?: boolean) => {
    const isRed = card.suit === Suits.HEARTS || card.suit === Suits.DIAMONDS;
    const suitSymbols = {
      [Suits.CLUBS]: "♣",
      [Suits.DIAMONDS]: "♦",
      [Suits.HEARTS]: "♥",
      [Suits.SPADES]: "♠",
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={`
          w-24 h-36 sm:w-32 sm:h-48 bg-white rounded-xl border-2 shadow-2xl flex flex-col items-center justify-between p-3 transition-all duration-300
          ${disabled && !onClick ? "opacity-100 border-white/50" : disabled ? "opacity-40 cursor-not-allowed grayscale-[50%]" : "hover:-translate-y-4 cursor-pointer border-blue-400 hover:shadow-blue-500/20 scale-105"}
          ${isRed ? "text-red-600" : "text-gray-900"}
          ${selectingBottom3.find(c => c.suit === card.suit && c.rank === card.rank) ? "ring-4 ring-yellow-400 -translate-y-8 border-yellow-400" : ""}
        `}
      >
        <div className="w-full flex justify-start font-black text-2xl leading-none">{card.rank}</div>
        <div className="text-6xl sm:text-7xl drop-shadow-sm">{suitSymbols[card.suit]}</div>
        <div className="w-full flex justify-end font-black text-2xl leading-none rotate-180">{card.rank}</div>
      </button>
    );
  };

  return (
    <div className="w-full min-h-screen bg-green-900 text-white p-4 flex flex-col relative overflow-hidden">
      {/* Background felt texture effect */}
      <div className="absolute inset-0 opacity-30 pointer-events-none bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500/20 via-transparent to-black/60"></div>

      {/* Top Section: Scoreboard and Trump info */}
      <div className="flex justify-between items-start z-10 w-full max-w-7xl mx-auto">
        <div className="flex flex-col gap-3">
          <div className="bg-black/60 backdrop-blur-xl p-5 rounded-2xl border border-white/10 shadow-2xl text-left">
            <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-400 mb-3 font-black text-left">Match Progress</h2>
            <div className="flex gap-12">
              <div className="text-center">
                <p className="text-blue-400 font-black text-4xl tabular-nums drop-shadow-[0_0_10px_rgba(96,165,250,0.3)]">{gameState.team_scores[0]}</p>
                <p className={`text-[10px] uppercase font-bold mt-1 tracking-tighter transition-all ${gameState.my_seat_id % 2 === 0 ? 'text-blue-300 ring-1 ring-blue-400/50 px-2 py-0.5 rounded-md bg-blue-400/10' : 'text-gray-500'}`}>
                  Team Alpha {gameState.my_seat_id % 2 === 0 && "(YOU)"}
                </p>
              </div>
              <div className="w-px h-10 bg-white/10 self-center"></div>
              <div className="text-center">
                <p className="text-indigo-400 font-black text-4xl tabular-nums drop-shadow-[0_0_10px_rgba(129,140,248,0.3)]">{gameState.team_scores[1]}</p>
                <p className={`text-[10px] uppercase font-bold mt-1 tracking-tighter transition-all ${gameState.my_seat_id % 2 === 1 ? 'text-indigo-300 ring-1 ring-indigo-400/50 px-2 py-0.5 rounded-md bg-indigo-400/10' : 'text-gray-500'}`}>
                  Team Bravo {gameState.my_seat_id % 2 === 1 && "(YOU)"}
                </p>
              </div>
            </div>
          </div>

          {/* Current Hand Tricks Won */}
          <div className="bg-black/40 backdrop-blur-md px-4 py-2 rounded-xl border border-white/5 shadow-xl flex justify-between items-center group">
             <span className="text-[8px] uppercase font-black text-gray-500 tracking-widest group-hover:text-gray-300 transition-colors">Current Tricks</span>
             <div className="flex gap-4 items-center">
                <span className="text-blue-400 font-bold tabular-nums text-lg">{gameState.tricks_won[0] || 0}</span>
                <div className="w-px h-3 bg-white/10"></div>
                <span className="text-indigo-400 font-bold tabular-nums text-lg">{gameState.tricks_won[1] || 0}</span>
             </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-3">
          {(gameState.trump_suit || gameState.is_no_trump) && (
            <div className="bg-black/40 backdrop-blur-md px-6 py-3 rounded-2xl border border-white/10 flex items-center gap-3 shadow-xl animate-in fade-in zoom-in duration-500">
              <div className="flex flex-col items-end text-right">
                <span className="text-[8px] uppercase font-black text-gray-500 tracking-[0.3em] text-right">Trump Suit</span>
                <span className="text-sm font-bold text-gray-200">{gameState.is_no_trump ? "NO TRUMP" : gameState.trump_suit}</span>
              </div>
              <span className={`text-4xl drop-shadow-md ${gameState.is_no_trump ? "text-purple-400" : (gameState.trump_suit === Suits.HEARTS || gameState.trump_suit === Suits.DIAMONDS ? "text-red-500" : "text-blue-400")}`}>
                {gameState.is_no_trump ? "🚫" : (gameState.trump_suit === Suits.HEARTS ? "♥" : gameState.trump_suit === Suits.DIAMONDS ? "♦" : gameState.trump_suit === Suits.CLUBS ? "♣" : "♠")}
              </span>
            </div>
          )}
          <div className="bg-white/5 px-4 py-2 rounded-full text-xs font-black tracking-widest text-gray-400 border border-white/10">
            {playerName.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Main Table Area */}
      <div className="flex-1 flex items-center justify-center relative w-full h-full my-4">
        {/* The "Game Board" */}
        <div className="w-full max-w-[600px] aspect-square rounded-full border-[16px] border-green-950 bg-green-900/10 flex items-center justify-center relative shadow-[inset_0_0_200px_rgba(0,0,0,0.8),0_40px_100px_rgba(0,0,0,0.6)]">
          
          {/* Turned Up Card (during bidding) */}
          {gameState.current_bidder !== null && gameState.turned_up_card && (
            <div className="absolute z-10 scale-75 opacity-80 ring-4 ring-yellow-400/30 rounded-xl overflow-hidden shadow-2xl">
               {renderCard(gameState.turned_up_card)}
            </div>
          )}

          {/* Played Cards in Trick */}
          {gameState.current_trick.map((play, i) => {
            const relSeat = getRelativeSeat(play.player_id);
            // Positions relative to the table center point
            // Rel 2 (Partner) -> Top (0deg)
            // Rel 3 (Prev) -> Right (90deg)
            // Rel 0 (Me) -> Bottom (180deg)
            // Rel 1 (Next) -> Left (270deg)
            const seatRotations = [180, 270, 0, 90];
            const rotation = seatRotations[relSeat];
            
            return (
              <div 
                key={i} 
                className="absolute transition-all duration-700 ease-out z-20"
                style={{
                  transform: `rotate(${rotation}deg) translateY(-140px) rotate(-${rotation}deg)`
                }}
              >
                <div className="relative group scale-75 sm:scale-90">
                  <div className="absolute -inset-4 bg-white/10 rounded-2xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity text-center"></div>
                  {renderCard(play.card, undefined, true)}
                  <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-black bg-black/90 text-white px-3 py-1 rounded-full uppercase border border-white/20 shadow-2xl">
                    P{play.player_id}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Table Center Graphic */}
          {gameState.current_trick.length === 0 && (
             <div className="text-green-800/10 text-9xl font-black select-none pointer-events-none">
                EUCHRE
             </div>
          )}
        </div>

        {/* Bottom 3 Action Button */}
        {gameState.bottom_3_enabled && !gameState.bottom_3_used && gameState.bidding_phase === 1 && gameState.current_bidder === gameState.my_seat_id && isSelectingBottom3 && (
            <div className="absolute bottom-64 left-1/2 -translate-x-1/2 z-[110] flex flex-col items-center gap-4">
                {selectingBottom3.length === 3 ? (
                    <button 
                        onClick={handleBottom3Confirm}
                        className="bg-yellow-500 hover:bg-yellow-400 text-black font-black py-4 px-10 rounded-2xl shadow-2xl transition-all transform hover:scale-110 active:scale-95 animate-bounce"
                    >
                        CONFIRM BOTTOM 3 SWAP
                    </button>
                ) : (
                    <div className="bg-black/60 backdrop-blur-md px-6 py-3 rounded-full border border-yellow-500/30 text-yellow-400 text-[10px] font-black uppercase tracking-[0.2em] shadow-2xl">
                        Select 3 cards (9s or 10s) to swap
                    </div>
                )}
                <button 
                    onClick={() => { setIsSelectingBottom3(false); setSelectingBottom3([]); }}
                    className="text-white/60 hover:text-white text-xs font-bold uppercase tracking-widest bg-black/40 px-4 py-2 rounded-full backdrop-blur-sm border border-white/10 hover:bg-black/60 transition-all"
                >
                    Cancel Selection
                </button>
            </div>
        )}

        {/* Other Players Status Indicators */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-4 flex flex-col items-center">
            <div className={`w-14 h-14 rounded-full border-2 shadow-xl ${gameState.current_turn === (gameState.my_seat_id + 2) % 4 ? 'border-yellow-400 bg-yellow-400/20 shadow-yellow-400/30 ring-4 ring-yellow-400/20' : 'border-white/20 bg-black/60'} flex items-center justify-center font-black text-xl transition-all duration-500`}>
                P{(gameState.my_seat_id + 2) % 4}
            </div>
            <p className="text-[10px] uppercase mt-2 font-black text-gray-500 tracking-tighter">Partner</p>
        </div>
        <div className="absolute left-4 sm:left-12 top-1/2 -translate-y-1/2 flex flex-col items-center">
            <div className={`w-14 h-14 rounded-full border-2 shadow-xl ${gameState.current_turn === (gameState.my_seat_id + 1) % 4 ? 'border-yellow-400 bg-yellow-400/20 shadow-yellow-400/30 ring-4 ring-yellow-400/20' : 'border-white/20 bg-black/60'} flex items-center justify-center font-black text-xl transition-all duration-500`}>
                P{(gameState.my_seat_id + 1) % 4}
            </div>
            <p className="text-[10px] uppercase mt-2 font-black text-gray-500 tracking-tighter">Opponent</p>
        </div>
        <div className="absolute right-4 sm:right-12 top-1/2 -translate-y-1/2 flex flex-col items-center">
            <div className={`w-14 h-14 rounded-full border-2 shadow-xl ${gameState.current_turn === (gameState.my_seat_id + 3) % 4 ? 'border-yellow-400 bg-yellow-400/20 shadow-yellow-400/30 ring-4 ring-yellow-400/20' : 'border-white/20 bg-black/60'} flex items-center justify-center font-black text-xl transition-all duration-500`}>
                P{(gameState.my_seat_id + 3) % 4}
            </div>
            <p className="text-[10px] uppercase mt-2 font-black text-gray-500 tracking-tighter">Opponent</p>
        </div>
      </div>

      {/* Bidding UI - Centered Overlay */}
      {gameState.current_bidder !== null && 
       gameState.current_bidder === gameState.my_seat_id && 
       gameState.bidding_phase !== 3 && !isSelectingBottom3 && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/10 p-4 animate-in fade-in duration-300">
          <div className="bg-gray-900/95 p-10 rounded-[2.5rem] shadow-3xl border border-blue-500/20 w-full max-w-lg relative overflow-hidden text-center">

            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent"></div>
            
            <h2 className="text-3xl font-black mb-1 text-center text-white tracking-tight">
              {gameState.bidding_phase === 1 ? "Round 1: Order It Up?" : "Round 2: Name Trump"}
            </h2>
            <p className="text-gray-500 text-center mb-8 text-sm uppercase tracking-[0.2em] font-bold">
              {gameState.bidding_phase === 1 
                ? `Dealer has ${gameState.turned_up_card?.suit}`
                : "Choose a different suit"}
            </p>
            
            <div className="grid grid-cols-2 gap-6 mb-10">
              {gameState.bidding_phase === 1 ? (
                // Round 1: Only the turned up suit is allowed
                <>
                <button 
                  onClick={() => handleBid(gameState.turned_up_card?.suit || null)}
                  className="col-span-2 group bg-blue-600/20 hover:bg-blue-600/40 p-10 rounded-3xl font-black flex flex-col items-center gap-4 transition-all border border-blue-500/40 hover:scale-105 shadow-2xl active:scale-95"
                >
                   <span className={`text-8xl transition-transform group-hover:scale-110 ${gameState.turned_up_card?.suit === Suits.HEARTS || gameState.turned_up_card?.suit === Suits.DIAMONDS ? "text-red-500" : "text-blue-400"}`}>
                    {gameState.turned_up_card?.suit === Suits.HEARTS ? "♥" : gameState.turned_up_card?.suit === Suits.DIAMONDS ? "♦" : gameState.turned_up_card?.suit === Suits.CLUBS ? "♣" : "♠"}
                  </span>
                  <span className="text-xl uppercase tracking-[0.3em] text-white">Pick It Up</span>
                </button>

                {gameState.bottom_3_enabled && !gameState.bottom_3_used && (
                    <button 
                        onClick={() => setIsSelectingBottom3(true)}
                        disabled={gameState.hand.filter(c => c.rank === 9 || c.rank === 10 || c.rank === "NINE" || c.rank === "TEN").length < 3}
                        className="col-span-2 bg-yellow-600/20 hover:bg-yellow-600/40 disabled:opacity-30 disabled:cursor-not-allowed p-4 rounded-2xl font-black transition-all border border-yellow-500/40 hover:scale-105 mt-2 flex items-center justify-center gap-3"
                    >
                        <Plus size={20} className="text-yellow-400" />
                        <span className="text-sm uppercase tracking-[0.2em] text-white">Perform Bottom 3</span>
                    </button>
                )}
                </>
              ) : (
                // Round 2: All suits EXCEPT the turned up one + No Trump
                <>
                  {Object.values(Suits)
                    .filter(s => s !== gameState.turned_up_card?.suit)
                    .map(s => (
                      <button 
                        key={s}
                        onClick={() => handleBid(s)}
                        className="group bg-white/5 hover:bg-blue-600/20 p-6 rounded-3xl font-black flex flex-col items-center gap-3 transition-all border border-white/5 hover:border-blue-500/40 hover:scale-105 shadow-lg active:scale-95"
                      >
                        <span className={`text-6xl transition-transform group-hover:scale-110 ${s === Suits.HEARTS || s === Suits.DIAMONDS ? "text-red-500" : "text-blue-400"}`}>
                          {s === Suits.HEARTS ? "♥" : s === Suits.DIAMONDS ? "♦" : s === Suits.CLUBS ? "♣" : "♠"}
                        </span>
                        <span className="text-[10px] uppercase tracking-[0.3em] text-gray-400 group-hover:text-white transition-colors">{s}</span>
                      </button>
                    ))}
                  
                  <button 
                    onClick={() => sendAction({ type: "call_trump", suit: null, is_no_trump: true })}
                    className="col-span-2 group bg-purple-600/20 hover:bg-purple-600/40 p-8 rounded-3xl font-black flex flex-col items-center gap-2 transition-all border border-purple-500/40 hover:scale-105 shadow-xl active:scale-95 mt-2"
                  >
                    <span className="text-5xl group-hover:scale-110 transition-transform">🚫</span>
                    <span className="text-lg uppercase tracking-[0.3em] text-white">No Trump</span>
                  </button>
                </>
              )}
            </div>

            <button 
              onClick={() => handleBid(null)}
              className="w-full bg-white/10 hover:bg-gray-700 py-5 rounded-2xl font-black transition-all uppercase tracking-[0.4em] text-xs border border-white/5 hover:border-white/20 active:bg-black/40"
            >
              Pass Action
            </button>
          </div>
        </div>
      )}

      {/* Bottom Section: User Hand and Status */}
      <div className="z-10 mt-auto flex flex-col items-center pb-8">
        {error && (
            <div className="mb-6 animate-bounce">
                <div className="text-red-400 text-xs font-black bg-red-950/80 px-6 py-3 rounded-full border border-red-500/30 backdrop-blur-xl shadow-2xl uppercase tracking-widest flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    {error}
                </div>
            </div>
        )}
        
        <div className="flex flex-col items-center gap-8 w-full">
            <div className={`px-8 py-3 rounded-full border-2 transition-all duration-700 ${gameState.current_turn === gameState.my_seat_id || (gameState.bidding_phase === 3 && gameState.my_seat_id === gameState.dealer_id) ? 'border-yellow-400 bg-yellow-400/10 shadow-[0_0_50px_rgba(250,204,21,0.2)]' : 'border-white/5 bg-black/40'}`}>
                <span className={`font-black text-xs uppercase tracking-[0.4em] ${gameState.current_turn === gameState.my_seat_id || (gameState.bidding_phase === 3 && gameState.my_seat_id === gameState.dealer_id) ? 'text-yellow-400' : 'text-gray-600'}`}>
                    {(gameState.current_turn === gameState.my_seat_id || (gameState.bidding_phase === 3 && gameState.my_seat_id === gameState.dealer_id)) 
                        ? (gameState.bidding_phase === 3 ? "• Choose Card to Discard •" : "• Your Turn •") 
                        : "Waiting for Opponent"}
                </span>
            </div>

            <div className="flex -space-x-8 sm:-space-x-12 hover:space-x-2 transition-all duration-500 group">
                {gameState.hand.map((card, i) => {
                    const isMyTurnToPlay = gameState.current_turn === gameState.my_seat_id;
                    const isMyTurnToDiscard = gameState.bidding_phase === 3 && gameState.my_seat_id === gameState.dealer_id;
                    const isMyTurnToBidRound1 = gameState.bidding_phase === 1 && gameState.current_bidder === gameState.my_seat_id;
                    const canBottom3 = gameState.bottom_3_enabled && !gameState.bottom_3_used && isMyTurnToBidRound1;
                    
                    const isDisabled = !(isMyTurnToPlay || isMyTurnToDiscard || canBottom3);

                    return (
                        <div 
                            key={i} 
                            className="hover:z-50 transition-all duration-300 first:ml-0"
                            style={{
                                transform: `rotate(${(i - (gameState.hand.length - 1) / 2) * 4}deg) translateY(${Math.abs(i - (gameState.hand.length - 1) / 2) * 4}px)`
                            }}
                        >
                            {renderCard(
                                card, 
                                () => handleCardClick(card), 
                                isDisabled
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
      </div>

      {/* Game Over Overlay */}
      {gameState.is_over && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/90 backdrop-blur-3xl animate-in fade-in zoom-in duration-500">
          <div className="text-center p-12 max-w-2xl w-full">
            <div className={`text-[120px] mb-8 animate-bounce transition-colors ${myTeamWins ? "text-yellow-400 drop-shadow-[0_0_30px_rgba(250,204,21,0.5)]" : "text-gray-600"}`}>
              {myTeamWins ? "🏆" : "💀"}
            </div>
            
            <h1 className="text-7xl font-black mb-4 tracking-tighter text-white">
              {myTeamWins ? "VICTORY" : "DEFEAT"}
            </h1>
            
            <p className="text-gray-400 text-sm uppercase tracking-[0.5em] mb-12 font-black">
              {alphaWins ? "Team Alpha" : "Team Bravo"} has won the match
            </p>

            <div className="bg-white/5 rounded-3xl p-10 border border-white/10 mb-12 flex justify-around items-center">
              <div className="text-center">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-2 font-bold">Team Alpha</p>
                <p className={`text-6xl font-black tabular-nums ${alphaWins ? "text-blue-400" : "text-gray-600"}`}>{alphaScore}</p>
              </div>
              <div className="h-12 w-px bg-white/10"></div>
              <div className="text-center">
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-2 font-bold">Team Bravo</p>
                <p className={`text-6xl font-black tabular-nums ${bravoWins ? "text-indigo-400" : "text-gray-600"}`}>{bravoScore}</p>
              </div>
            </div>

            <button
              onClick={handleReturnToLobby}
              className="group relative px-12 py-5 bg-blue-600 hover:bg-blue-500 rounded-2xl transition-all duration-300 transform hover:scale-105 active:scale-95 shadow-[0_20px_50px_rgba(37,99,235,0.4)]"
            >
              <span className="relative z-10 text-white font-black uppercase tracking-[0.3em] text-sm">Return to Lobby</span>
              <div className="absolute inset-0 bg-white/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
