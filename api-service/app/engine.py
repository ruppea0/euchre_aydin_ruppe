import random
from typing import List, Optional, Dict, Tuple
from app.models import Card, Suit, Rank


class Deck:
    def __init__(self) -> None:
        self.cards = [
            Card(suit, rank) for suit in Suit for rank in Rank if rank >= Rank.NINE
        ]

    def to_dict(self) -> dict:
        return {"cards": [c.to_dict() for c in self.cards]}

    @classmethod
    def from_dict(cls, data: dict) -> "Deck":
        instance = cls()
        instance.cards = [Card.from_dict(c) for c in data["cards"]]
        return instance

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> List[List[Card]]:
        """Deals 5 cards to each of 4 players."""
        self.shuffle()
        return [self.cards[i * 5 : (i + 1) * 5] for i in range(4)]


class Player:
    def __init__(self, name: str, seat_id: int) -> None:
        self.name = name
        self.seat_id = seat_id
        self.hand: List[Card] = []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "seat_id": self.seat_id,
            "hand": [c.to_dict() for c in self.hand],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        instance = cls(data["name"], data["seat_id"])
        instance.hand = [Card.from_dict(c) for c in data["hand"]]
        return instance

    def __repr__(self) -> str:
        return f"Player({self.name}, seat={self.seat_id})"


class Trick:
    def __init__(
        self, leader_id: int, trump_suit: Optional[Suit], active_seats: List[int]
    ) -> None:
        self.leader_id = leader_id
        self.trump_suit = trump_suit
        self.active_seats = active_seats
        self.cards_played: List[Tuple[int, Card]] = []  # List of (player_id, card)

    def to_dict(self) -> dict:
        return {
            "leader_id": self.leader_id,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "active_seats": self.active_seats,
            "cards_played": [
                {"player_id": p_id, "card": c.to_dict()}
                for p_id, c in self.cards_played
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trick":
        instance = cls(
            data["leader_id"],
            Suit(data["trump_suit"]) if data["trump_suit"] else None,
            data["active_seats"],
        )
        instance.cards_played = [
            (cp["player_id"], Card.from_dict(cp["card"])) for cp in data["cards_played"]
        ]
        return instance

    @property
    def lead_suit(self) -> Optional[Suit]:
        if not self.cards_played:
            return None
        return self.cards_played[0][1].get_effective_suit(self.trump_suit)

    def play_card(self, player_id: int, card: Card, player_hand: List[Card]) -> None:
        """Validates and plays a card."""
        if player_id not in self.active_seats:
            raise ValueError(f"Player {player_id} is not active in this hand.")

        if not self.is_legal_move(card, player_hand):
            raise ValueError("Illegal move: Must follow suit if possible.")

        self.cards_played.append((player_id, card))

    def is_legal_move(self, card: Card, player_hand: List[Card]) -> bool:
        """Checks if playing the card is legal."""
        lead_suit = self.lead_suit
        if lead_suit is None:
            return True  # Anything is legal as the lead card

        effective_suit = card.get_effective_suit(self.trump_suit)
        if effective_suit == lead_suit:
            return True

        # If not following suit, check if the player has any cards of the lead suit
        has_lead_suit = any(
            c.get_effective_suit(self.trump_suit) == lead_suit for c in player_hand
        )

        return not has_lead_suit

    def get_winner(self) -> int:
        """Returns the seat_id of the winner of this trick."""
        if len(self.cards_played) < len(self.active_seats):
            raise ValueError("Trick is not complete.")

        best_card = self.cards_played[0][1]
        winner_id = self.cards_played[0][0]
        lead_suit = self.lead_suit

        for player_id, card in self.cards_played[1:]:
            if card.get_value(self.trump_suit, lead_suit) > best_card.get_value(
                self.trump_suit, lead_suit
            ):
                best_card = card
                winner_id = player_id

        return winner_id


class Hand:
    """Represents a single hand of 5 tricks."""

    def __init__(
        self,
        players: List[Player],
        dealer_id: int,
        trump_suit: Optional[Suit],
        maker_id: int,
        alone: bool = False,
    ) -> None:
        self.players = players
        self.dealer_id = dealer_id
        self.trump_suit = trump_suit
        self.maker_id = maker_id  # Player who called trump
        self.alone = alone
        self.tricks: List[Trick] = []
        self.scores = {0: 0, 1: 0}  # Team 0 (seats 0, 2) and Team 1 (seats 1, 3)

        self.active_seats = [0, 1, 2, 3]
        if self.alone:
            partner_seat = (self.maker_id + 2) % 4
            self.active_seats.remove(partner_seat)

    def to_dict(self) -> dict:
        return {
            "dealer_id": self.dealer_id,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "maker_id": self.maker_id,
            "alone": self.alone,
            "tricks": [t.to_dict() for t in self.tricks],
            "scores": {str(k): v for k, v in self.scores.items()},
            "active_seats": self.active_seats,
        }

    @classmethod
    def from_dict(cls, data: dict, players: List[Player]) -> "Hand":
        instance = cls(
            players,
            data["dealer_id"],
            Suit(data["trump_suit"]) if data.get("trump_suit") else None,
            data["maker_id"],
            data["alone"],
        )
        instance.tricks = [Trick.from_dict(t) for t in data["tricks"]]
        instance.scores = {int(k): v for k, v in data["scores"].items()}
        instance.active_seats = data["active_seats"]
        return instance

    def start_trick(self, leader_id: int) -> Trick:
        # If leader is sitting out, the leader should be the next person
        current_leader = leader_id
        while current_leader not in self.active_seats:
            current_leader = (current_leader + 1) % 4

        trick = Trick(current_leader, self.trump_suit, self.active_seats)
        self.tricks.append(trick)
        return trick

    def record_trick_winner(self, winner_id: int) -> None:
        team = winner_id % 2
        self.scores[team] += 1

    def get_hand_score(self) -> Dict[int, int]:
        """
        Calculates the points awarded for the hand.
        Points:
        - Maker team gets 3 or 4 tricks: 1 point
        - Maker team gets 5 tricks: 2 points (4 if alone)
        - Defending team gets 3+ tricks: 2 points (Euchred)
        """
        maker_team = self.maker_id % 2
        maker_tricks = self.scores[maker_team]

        if maker_tricks >= 3:
            if maker_tricks == 5:
                return {maker_team: 4 if self.alone else 2, 1 - maker_team: 0}
            return {maker_team: 1, 1 - maker_team: 0}
        else:
            # Euchred!
            return {maker_team: 0, 1 - maker_team: 2}
