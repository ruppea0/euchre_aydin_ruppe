from typing import List, Dict, Optional, Tuple
from app.models import Suit, Card, Rank
from app.engine import Deck, Player, Hand
from app.bidding import Bidding, BidPhase


class Game:
    def __init__(
        self,
        player_names: List[str],
        win_threshold: int = 2,
        screw_the_dealer: bool = False,
        bottom_3_enabled: bool = False,
        lobby_id: str = "default",
    ) -> None:
        if len(player_names) != 4:
            raise ValueError("Euchre requires exactly 4 players.")

        self.players = [Player(name, i) for i, name in enumerate(player_names)]
        self.win_threshold = win_threshold
        self.screw_the_dealer = screw_the_dealer
        self.bottom_3_enabled = bottom_3_enabled
        self.lobby_id = lobby_id

        self.team_scores = {0: 0, 1: 0}
        self.dealer_id = 0  # Start with player 0 as dealer

        self.current_hand: Optional[Hand] = None
        self.current_bidding: Optional[Bidding] = None
        self.deck = Deck()
        self.is_over = False

    def to_dict(self) -> dict:
        return {
            "player_names": [p.name for p in self.players],
            "players": [p.to_dict() for p in self.players],
            "win_threshold": self.win_threshold,
            "screw_the_dealer": self.screw_the_dealer,
            "bottom_3_enabled": self.bottom_3_enabled,
            "lobby_id": self.lobby_id,
            "team_scores": {str(k): v for k, v in self.team_scores.items()},
            "dealer_id": self.dealer_id,
            "current_hand": self.current_hand.to_dict() if self.current_hand else None,
            "current_bidding": (
                self.current_bidding.to_dict() if self.current_bidding else None
            ),
            "deck": self.deck.to_dict(),
            "is_over": self.is_over,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        instance = cls(
            data["player_names"],
            data["win_threshold"],
            data["screw_the_dealer"],
            data.get("bottom_3_enabled", False),
            data.get("lobby_id", "default"),
        )
        instance.players = [Player.from_dict(p) for p in data["players"]]
        instance.team_scores = {int(k): v for k, v in data["team_scores"].items()}
        instance.dealer_id = data["dealer_id"]
        instance.current_hand = (
            Hand.from_dict(data["current_hand"], instance.players)
            if data["current_hand"]
            else None
        )
        instance.current_bidding = (
            Bidding.from_dict(data["current_bidding"])
            if data["current_bidding"]
            else None
        )
        instance.deck = Deck.from_dict(data["deck"])
        instance.is_over = data["is_over"]
        return instance

    def start_new_hand(self) -> Tuple[List[List[Card]], Card]:
        """Starts a new hand: deals cards and turns up the top card."""
        hands = self.deck.deal()
        for i, player_hand in enumerate(hands):
            self.players[i].hand = player_hand

        # Top card is the next card in the deck after dealing 20 cards
        turned_up_card = self.deck.cards[20]
        self.current_bidding = Bidding(
            self.dealer_id, turned_up_card, self.screw_the_dealer
        )
        self.current_hand = None

        return hands, turned_up_card

    def perform_bottom_3(self, player_id: int, cards_to_swap: List[Card]) -> None:
        """Implements the Bottom 3 house rule."""
        if not self.bottom_3_enabled:
            raise ValueError("Bottom 3 rule is not enabled.")
        if not self.current_bidding:
            raise ValueError("Bidding is not active.")
        if self.current_bidding.phase != BidPhase.ROUND_1:
            raise ValueError("Bottom 3 can only be used during Round 1 of bidding.")
        if self.current_bidding.bottom_3_used:
            raise ValueError("Bottom 3 has already been used this hand.")
        if player_id != self.current_bidding.current_bidder:
            raise ValueError("You can only use Bottom 3 during your turn to bid.")
        if len(cards_to_swap) != 3:
            raise ValueError("You must select exactly 3 cards to swap.")

        player = self.players[player_id]
        
        # Validate that selected cards are 9s and 10s and in the player's hand
        for card in cards_to_swap:
            if card not in player.hand:
                raise ValueError(f"Card {card} is not in your hand.")
            if card.rank not in [Rank.NINE, Rank.TEN]:
                raise ValueError(f"Card {card} is not a 9 or 10.")

        # Identifiy the 3 face-down cards (the kitty)
        # Cards 20 is turned up, 21, 22, 23 are face down.
        kitty_cards = self.deck.cards[21:24]

        # Swap cards
        # We use a loop to remove exactly one instance of each card in cards_to_swap
        for card in cards_to_swap:
            # We want to remove the specific card that matches by value
            # Since player.hand.remove(card) uses __eq__, it's fine as long as 
            # we don't have duplicate cards in a real deck.
            player.hand.remove(card)
        
        player.hand.extend(kitty_cards)
        
        # Mark as used and PASS the turn for Round 1
        self.current_bidding.bottom_3_used = True
        self.current_bidding.call(player_id, None)

    def apply_dealer_discard(self, player_id: int, discard_card: Card) -> None:
        """Dealer picks up the turned-up card and discards one."""
        if not self.current_bidding or self.current_bidding.phase != BidPhase.DEALER_DISCARD:
            raise ValueError("It is not time for dealer to discard.")
        if player_id != self.dealer_id:
            raise ValueError("Only the dealer can discard.")

        dealer = self.players[self.dealer_id]
        
        # Add turned-up card to dealer's hand
        dealer.hand.append(self.current_bidding.turned_up_card)
        
        # Remove discard_card from dealer's hand
        if discard_card not in dealer.hand:
            raise ValueError("Card not in dealer's hand.")
        
        dealer.hand.remove(discard_card)
        
        # Set trump and start first trick
        self.set_trump(
            self.current_bidding.maker_id,
            self.current_bidding.trump_suit,
            self.current_bidding.alone
        )

    def set_trump(self, maker_id: int, suit: Optional[Suit], alone: bool = False) -> None:
        """Sets the trump suit and initializes the Hand."""
        self.current_hand = Hand(self.players, self.dealer_id, suit, maker_id, alone)
        self.current_bidding = None

    def finish_hand(self) -> Dict[int, int]:
        """Calculates score and prepares for next dealer."""
        if not self.current_hand:
            raise ValueError("No active hand to finish.")

        hand_points = self.current_hand.get_hand_score()
        for team, points in hand_points.items():
            self.team_scores[team] += points

        if (
            self.team_scores[0] >= self.win_threshold
            or self.team_scores[1] >= self.win_threshold
        ):
            self.is_over = True

        self.dealer_id = (self.dealer_id + 1) % 4
        return hand_points
