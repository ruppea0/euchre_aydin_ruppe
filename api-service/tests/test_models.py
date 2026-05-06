from app.models import Card, Suit, Rank


def test_card_equality():
    c1 = Card(Suit.HEARTS, Rank.ACE)
    c2 = Card(Suit.HEARTS, Rank.ACE)
    c3 = Card(Suit.SPADES, Rank.ACE)
    assert c1 == c2
    assert c1 != c3


def test_effective_suit_no_trump():
    c = Card(Suit.DIAMONDS, Rank.JACK)
    assert c.get_effective_suit(None) == Suit.DIAMONDS


def test_effective_suit_with_trump():
    # Jack of Diamonds is Left Bower when Hearts is trump
    c = Card(Suit.DIAMONDS, Rank.JACK)
    assert c.get_effective_suit(Suit.HEARTS) == Suit.HEARTS

    # Jack of Hearts is Right Bower, its effective suit is still Hearts
    c2 = Card(Suit.HEARTS, Rank.JACK)
    assert c2.get_effective_suit(Suit.HEARTS) == Suit.HEARTS

    # Non-Jack card
    c3 = Card(Suit.DIAMONDS, Rank.ACE)
    assert c3.get_effective_suit(Suit.HEARTS) == Suit.DIAMONDS


def test_card_values_no_trump():
    trump = None
    lead = Suit.CLUBS

    ace_clubs = Card(Suit.CLUBS, Rank.ACE)
    nine_clubs = Card(Suit.CLUBS, Rank.NINE)
    jack_spades = Card(Suit.SPADES, Rank.JACK)  # Not a bower
    ace_hearts = Card(Suit.HEARTS, Rank.ACE)

    # In No Trump, lead suit and rank are all that matter
    assert ace_clubs.get_value(trump, lead) == 64
    assert nine_clubs.get_value(trump, lead) == 59
    assert jack_spades.get_value(trump, lead) == 11
    assert ace_hearts.get_value(trump, lead) == 14


def test_card_values():
    trump = Suit.HEARTS
    lead = Suit.CLUBS

    right_bower = Card(Suit.HEARTS, Rank.JACK)
    left_bower = Card(Suit.DIAMONDS, Rank.JACK)
    ace_trump = Card(Suit.HEARTS, Rank.ACE)
    nine_trump = Card(Suit.HEARTS, Rank.NINE)
    ace_lead = Card(Suit.CLUBS, Rank.ACE)
    nine_lead = Card(Suit.CLUBS, Rank.NINE)
    other_card = Card(Suit.SPADES, Rank.ACE)

    # Value order: Right > Left > Ace Trump > Nine Trump > Ace Lead > Nine Lead
    assert right_bower.get_value(trump, lead) == 1000
    assert left_bower.get_value(trump, lead) == 999
    assert ace_trump.get_value(trump, lead) == 114
    assert nine_trump.get_value(trump, lead) == 109
    assert ace_lead.get_value(trump, lead) == 64
    assert nine_lead.get_value(trump, lead) == 59
    assert other_card.get_value(trump, lead) == 14
