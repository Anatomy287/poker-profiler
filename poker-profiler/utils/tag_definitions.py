TENDENCY_TAGS = {
    "Preflop": [
        "3bet-light",
        "limp-call",
        "limp-fold",
        "open-too-wide",
        "squeeze",
        "flat-ip",
    ],
    "Postflop — Fold Tendencies": [
        "fold-flop-cbet",
        "fold-turn-cbet",
        "fold-river-bet",
        "fold-to-raise",
    ],
    "Postflop — Call Tendencies": [
        "call-wide-flop",
        "call-wide-turn",
        "call-wide-river",
        "call-station",
    ],
    "Bet Sizing Tells": [
        "overbet-bluff",
        "small-bet-value",
        "small-bet-bluff",
        "overbet-value",
        "sizing-polarized",
        "sizing-inverted",
    ],
    "General Postflop": [
        "donk-bet",
        "slowplay",
        "probe-bet",
        "check-raise",
        "bluff-river",
        "value-thin",
        "tilt-play",
    ],
}

ALL_TAGS = [tag for tags in TENDENCY_TAGS.values() for tag in tags]

TAG_DESCRIPTIONS = {
    "3bet-light": "3-bet without premium hand",
    "limp-call": "Limped then called a raise preflop",
    "limp-fold": "Limped and folded to a raise",
    "open-too-wide": "Opened from early position with weak hand",
    "squeeze": "3-bet into a caller",
    "flat-ip": "Called in position instead of 3-betting strong hand",
    "fold-flop-cbet": "Folded to continuation bet on flop",
    "fold-turn-cbet": "Folded to continuation bet on turn",
    "fold-river-bet": "Folded to river bet",
    "fold-to-raise": "Folded when facing a raise on any street",
    "call-wide-flop": "Called flop bet with weak holding",
    "call-wide-turn": "Called turn bet with weak/drawing hand",
    "call-wide-river": "Called river bet with marginal hand",
    "call-station": "Pattern of calling down across multiple streets",
    "overbet-bluff": "Bet significantly over pot as a bluff",
    "small-bet-value": "Under-bet or min-bet strong hand",
    "small-bet-bluff": "Small bet as a bluff (blocking bet)",
    "overbet-value": "Large bet with strong hand (no sizing tell)",
    "sizing-polarized": "Consistent large = strong / small = weak",
    "sizing-inverted": "Large = bluff / small = value (exploitable tell)",
    "donk-bet": "Led into preflop aggressor",
    "slowplay": "Checked or under-bet strong hand",
    "probe-bet": "Bet after PFR checked back",
    "check-raise": "Check-raised",
    "bluff-river": "Bluffed on the river",
    "value-thin": "Made thin value bet at showdown",
    "tilt-play": "Played poorly after a bad beat or loss",
}

POSITIONS = ["BTN", "CO", "HJ", "MP", "UTG+1", "UTG", "SB", "BB"]
STREETS = ["Preflop", "Flop", "Turn", "River"]
RESULTS = ["Won", "Lost", "Split", "No showdown"]
PLAYING_STYLES = ["Unknown", "Nit", "Tight-Passive", "Calling Station", "TAG", "LAG", "Maniac"]

SIZING_TELL_TAGS = {"overbet-bluff", "small-bet-value", "small-bet-bluff", "sizing-polarized", "sizing-inverted"}
PRIORITY_TAGS = ["fold-flop-cbet", "fold-turn-cbet", "call-wide-flop", "call-wide-turn", "sizing-inverted", "overbet-bluff"]
