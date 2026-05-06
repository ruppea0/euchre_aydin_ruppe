from enum import Enum, IntEnum
from typing import Optional


class Suit(Enum):
    CLUBS = "CLUBS"
    DIAMONDS = "DIAMONDS"
    HEARTS = "HEARTS"
    SPADES = "SPADES"

    @property
    def color(self) -> str:
        if self in [Suit.CLUBS, Suit.SPADES]:
            return "BLACK"
        return "RED"

    @property
    def partner_suit(self) -> "Suit":
        if self == Suit.CLUBS:
            return Suit.SPADES
        if self == Suit.SPADES:
            return Suit.CLUBS
        if self == Suit.HEARTS:
            return Suit.DIAMONDS
        if self == Suit.DIAMONDS:
            return Suit.HEARTS
        raise ValueError("Invalid suit")


class Rank(IntEnum):
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card:
    def __init__(self, suit: Suit, rank: Rank) -> None:
        self.suit = suit
        self.rank = rank

    def to_dict(self) -> dict:
        return {"suit": self.suit.value, "rank": self.rank.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(Suit(data["suit"]), Rank(data["rank"]))

    def __repr__(self) -> str:
        return f"{self.rank.name} of {self.suit.value}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def get_effective_suit(self, trump_suit: Optional[Suit]) -> Suit:
        """Returns the suit of the card, accounting for the Left Bower."""
        if (
            trump_suit
            and self.rank == Rank.JACK
            and self.suit == trump_suit.partner_suit
        ):
            return trump_suit
        return self.suit

    def get_value(self, trump_suit: Optional[Suit], lead_suit: Optional[Suit]) -> int:
        """
        Returns a numerical value for comparing cards in a trick.
        Values are calculated based on trump and lead suit.
        """
        effective_suit = self.get_effective_suit(trump_suit)

        # Right Bower
        if trump_suit and self.rank == Rank.JACK and self.suit == trump_suit:
            return 1000

        # Left Bower
        if (
            trump_suit
            and self.rank == Rank.JACK
            and self.suit == trump_suit.partner_suit
        ):
            return 999

        # Other Trump cards
        if trump_suit and effective_suit == trump_suit:
            return 100 + self.rank.value

        # Lead suit cards
        if lead_suit and effective_suit == lead_suit:
            return 50 + self.rank.value

        # Other cards
        return self.rank.value
