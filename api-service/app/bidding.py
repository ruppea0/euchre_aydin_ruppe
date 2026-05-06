from enum import Enum
from typing import Optional
from app.models import Card, Suit


class BidPhase(Enum):
    ROUND_1 = 1  # Ordering up the turned-up card
    ROUND_2 = 2  # Calling any suit other than the turned-up one
    DEALER_DISCARD = 3  # Dealer must pick up the turned-up card and discard one
    COMPLETED = 4


class Bidding:
    def __init__(
        self, dealer_id: int, turned_up_card: Card, screw_the_dealer: bool = False
    ):
        self.dealer_id = dealer_id
        self.turned_up_card = turned_up_card
        self.screw_the_dealer = screw_the_dealer
        self.phase = BidPhase.ROUND_1
        self.current_bidder = (dealer_id + 1) % 4
        self.trump_suit: Optional[Suit] = None
        self.maker_id: Optional[int] = None
        self.alone: bool = False
        self.is_no_trump: bool = False
        self.bottom_3_used: bool = False

    def to_dict(self) -> dict:
        return {
            "dealer_id": self.dealer_id,
            "turned_up_card": self.turned_up_card.to_dict(),
            "screw_the_dealer": self.screw_the_dealer,
            "phase": self.phase.value,
            "current_bidder": self.current_bidder,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "maker_id": self.maker_id,
            "alone": self.alone,
            "is_no_trump": self.is_no_trump,
            "bottom_3_used": self.bottom_3_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bidding":
        instance = cls(
            data["dealer_id"],
            Card.from_dict(data["turned_up_card"]),
            data["screw_the_dealer"],
        )
        instance.phase = BidPhase(data["phase"])
        instance.current_bidder = data["current_bidder"]
        instance.trump_suit = (
            Suit(data["trump_suit"]) if data.get("trump_suit") else None
        )
        instance.maker_id = data["maker_id"]
        instance.alone = data["alone"]
        instance.is_no_trump = data.get("is_no_trump", False)
        instance.bottom_3_used = data.get("bottom_3_used", False)
        return instance

    def call(
        self,
        player_id: int,
        suit: Optional[Suit],
        alone: bool = False,
        is_no_trump: bool = False,
    ) -> bool:
        """
        Processes a bid. Returns True if trump is set, False if the player passes.
        """
        if player_id != self.current_bidder:
            raise ValueError(f"It's not player {player_id}'s turn to bid.")

        if self.phase == BidPhase.ROUND_1:
            if is_no_trump:
                raise ValueError("No Trump can only be called in Round 2.")
            if suit == self.turned_up_card.suit:
                self.trump_suit = suit
                self.maker_id = player_id
                self.alone = alone
                self.phase = BidPhase.DEALER_DISCARD
                self.current_bidder = self.dealer_id
                return True
            elif suit is None:
                if player_id == self.dealer_id:
                    self.phase = BidPhase.ROUND_2
                self.current_bidder = (self.current_bidder + 1) % 4
                return False
            else:
                raise ValueError(
                    "In Round 1, you can only call the turned-up suit or pass."
                )

        elif self.phase == BidPhase.ROUND_2:
            if is_no_trump:
                self.is_no_trump = True
                self.trump_suit = None
                self.maker_id = player_id
                self.alone = alone
                self.phase = BidPhase.COMPLETED
                return True

            if suit is not None:
                if suit == self.turned_up_card.suit:
                    raise ValueError(
                        "In Round 2, you cannot call the suit that was turned down."
                    )
                self.trump_suit = suit
                self.maker_id = player_id
                self.alone = alone
                self.phase = BidPhase.COMPLETED
                return True
            else:
                if player_id == self.dealer_id and self.screw_the_dealer:
                    raise ValueError("Screw the Dealer: Dealer must call a suit.")

                # If everyone passes in round 2, the hand is dead
                # (though usually dealer must call in some variations)
                if player_id == self.dealer_id:
                    self.phase = BidPhase.COMPLETED  # End of bidding, no trump set

                self.current_bidder = (self.current_bidder + 1) % 4
                return False

        return False
