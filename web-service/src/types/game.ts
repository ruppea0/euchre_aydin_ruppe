export type Suit = "CLUBS" | "DIAMONDS" | "HEARTS" | "SPADES";

export const Suits: Record<string, Suit> = {
  CLUBS: "CLUBS",
  DIAMONDS: "DIAMONDS",
  HEARTS: "HEARTS",
  SPADES: "SPADES",
};

export type RankValue = 9 | 10 | 11 | 12 | 13 | 14;

export const Ranks: Record<string, RankValue> = {
  NINE: 9,
  TEN: 10,
  JACK: 11,
  QUEEN: 12,
  KING: 13,
  ACE: 14,
};

export interface Card {
  suit: Suit;
  rank: string | number;
}

export interface GameStateUpdate {
  type: "game_state";
  my_seat_id: number;
  dealer_id: number;
  current_bidder: number | null;
  bidding_phase: number | null;
  turned_up_card: Card | null;
  trump_suit: Suit | null;
  maker_id: number | null;
  alone: boolean;
  team_scores: Record<number, number>;
  hand: Card[];
  tricks_won: Record<number, number>;
  current_trick: { player_id: number; card: Card }[];
  current_turn: number | null;
  is_over: boolean;
  win_threshold: number;
  is_no_trump: boolean;
  no_trump_enabled: boolean;
  bottom_3_enabled: boolean;
  bottom_3_used: boolean;
}

export interface LobbyUpdate {
  type: "lobby_update";
  lobby_id: string;
  players: string[];
  is_full: boolean;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export type Action = 
  | { type: "call_trump"; suit: Suit | null; alone?: boolean; is_no_trump?: boolean }
  | { type: "dealer_discard"; suit: Suit; rank: string }
  | { type: "play_card"; suit: Suit; rank: string }
  | { type: "bottom_3"; cards: Card[] };
