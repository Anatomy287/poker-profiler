"""
Page 1 — Hand Entry & Advisor
Single workflow: fill in hand → save to Airtable → get AI analysis.
"""

import streamlit as st
from datetime import date

from utils.tag_definitions import TENDENCY_TAGS, POSITIONS, STREETS, RESULTS
from utils.airtable_client import get_all_players, get_player_profile, save_hand_record
from utils.claude_client import analyse_hand

st.set_page_config(page_title="Poker Profiler", page_icon="🃏", layout="centered")

st.title("🃏 Hand Entry & Advisor")
st.caption("Enter a hand, save it, and get instant analysis based on the player's profile.")

# ---------------------------------------------------------------------------
# Load players for dropdown
# ---------------------------------------------------------------------------
try:
    players = get_all_players()
except Exception as e:
    st.error(f"Could not connect to Airtable: {e}")
    st.info("Check that your AIRTABLE_TOKEN and AIRTABLE_BASE_ID secrets are configured.")
    st.stop()

if not players:
    st.warning("No players in your database yet. Go to **Player Profiles** to add one first.")
    st.stop()

player_names = [p["name"] for p in players]
player_map = {p["name"]: p["id"] for p in players}

# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------
with st.form("hand_entry_form", clear_on_submit=False):

    # --- Player & context ---
    st.subheader("Player & Context")
    col1, col2 = st.columns(2)
    with col1:
        selected_player = st.selectbox("Opponent *", player_names)
        venue = st.text_input("Venue", placeholder="e.g. Crown Casino")
    with col2:
        hand_date = st.date_input("Date", value=date.today())
        stakes = st.text_input("Stakes", placeholder="e.g. $1/$2 NLH")

    col3, col4 = st.columns(2)
    with col3:
        hero_pos = st.selectbox("Your Position *", POSITIONS)
    with col4:
        villain_pos = st.selectbox("Villain Position *", POSITIONS)

    st.divider()

    # --- Entry mode toggle ---
    st.subheader("Hand Details")
    detailed_mode = st.toggle("Detailed Hand (full street-by-street)", value=False)

    street = st.selectbox("Street of Key Action *", STREETS)
    key_summary = st.text_area(
        "Key Decision Summary *",
        placeholder="e.g. Villain bet 3x pot on the river after checking flop and turn.",
        height=80,
    )
    your_action = st.text_area(
        "Your Action *",
        placeholder="e.g. I folded. / I called. / I raised to $120.",
        height=68,
    )

    col5, col6 = st.columns(2)
    with col5:
        pot_size = st.number_input("Pot Size (approx $)", min_value=0, step=5)
    with col6:
        result = st.selectbox("Result *", RESULTS)

    st.divider()

    # --- Tendency tags (grouped by category) ---
    st.subheader("Tendency Tags *")
    st.caption("Select at least one tag that describes what this hand reveals about the villain.")
    selected_tags: list[str] = []
    for category, tags in TENDENCY_TAGS.items():
        with st.expander(category, expanded=(category in ("Postflop — Fold Tendencies", "Bet Sizing Tells"))):
            cols = st.columns(2)
            for i, tag in enumerate(tags):
                if cols[i % 2].checkbox(tag, key=f"tag_{tag}"):
                    selected_tags.append(tag)

    notes = st.text_area(
        "Notes *",
        placeholder="What does this hand tell you about the villain? Minimum one sentence.",
        height=100,
    )

    st.divider()

    # --- Detailed fields (shown when toggle is on) ---
    if detailed_mode:
        st.subheader("Full Hand Detail")

        col7, col8 = st.columns(2)
        with col7:
            hero_cards = st.text_input("Your Hole Cards", placeholder="e.g. A♠K♥")
        with col8:
            villain_cards_shown = st.checkbox("Villain cards shown at showdown")
            villain_cards = st.text_input(
                "Villain Hole Cards",
                placeholder="e.g. 7♣2♦",
                disabled=not villain_cards_shown,
            )

        effective_stack = st.number_input("Effective Stack ($)", min_value=0, step=5)
        preflop_action = st.text_area("Preflop Action", placeholder="UTG raises $8, Hero calls BTN, Villain calls BB.", height=68)

        col9, col10 = st.columns([1, 3])
        with col9:
            flop = st.text_input("Flop", placeholder="A♥7♦2♣")
        with col10:
            flop_action = st.text_area("Flop Action", placeholder="Villain checks, Hero bets $15, Villain calls.", height=68)

        col11, col12 = st.columns([1, 3])
        with col11:
            turn = st.text_input("Turn", placeholder="Q♠")
        with col12:
            turn_action = st.text_area("Turn Action", placeholder="Villain leads $40.", height=68)

        col13, col14 = st.columns([1, 3])
        with col13:
            river = st.text_input("River", placeholder="9♣")
        with col14:
            river_action = st.text_area("River Action", placeholder="Villain bets $120 into $80 pot.", height=68)

        showdown = st.text_area("Showdown", placeholder="Villain tables 9♠9♦ for a set. Hero mucked.", height=68)

    submitted = st.form_submit_button("💾 Save & Analyse", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# Submit handler
# ---------------------------------------------------------------------------
if submitted:
    # Validation
    errors = []
    if not key_summary.strip():
        errors.append("Key Decision Summary is required.")
    if not your_action.strip():
        errors.append("Your Action is required.")
    if not selected_tags:
        errors.append("Select at least one Tendency Tag.")
    if not notes.strip():
        errors.append("Notes are required (minimum one sentence).")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    player_id = player_map[selected_player]

    # Build Airtable record
    hand_record: dict = {
        "Player": [player_id],
        "Date": hand_date.isoformat(),
        "Venue": venue,
        "Stakes": stakes,
        "Hero Position": hero_pos,
        "Villain Position": villain_pos,
        "Street of Key Action": street,
        "Key Decision Summary": key_summary.strip(),
        "Your Action": your_action.strip(),
        "Tendency Tags": selected_tags,
        "Pot Size": pot_size,
        "Result": result,
        "Notes": notes.strip(),
        "Entry Mode": "Detailed" if detailed_mode else "Quick",
    }

    if detailed_mode:
        hand_record.update({
            "Hero Hole Cards": hero_cards,
            "Villain Hole Cards": villain_cards if villain_cards_shown else "",
            "Effective Stack": effective_stack,
            "Preflop Action": preflop_action,
            "Flop": flop,
            "Flop Action": flop_action,
            "Turn": turn,
            "Turn Action": turn_action,
            "River": river,
            "River Action": river_action,
            "Showdown": showdown,
        })

    # Step 1: Save hand to Airtable (before analysis — record must not be lost if Claude fails)
    with st.spinner("Saving hand..."):
        try:
            save_hand_record(hand_record)
        except Exception as e:
            st.error(f"Failed to save hand to Airtable: {e}")
            st.stop()

    # Step 2: Fetch player profile (includes all hands + tag counts)
    with st.spinner("Loading player profile..."):
        try:
            profile = get_player_profile(player_id)
        except Exception as e:
            st.error(f"Hand saved, but could not fetch player profile: {e}")
            st.stop()

    # Low data warning
    if profile["hand_count"] < 5:
        st.warning(
            f"⚠ Only {profile['hand_count']} hand(s) recorded for {selected_player}. "
            "Analysis is speculative — build up more hands for reliable reads."
        )

    # Step 3: Get Claude analysis
    with st.spinner("Analysing hand..."):
        try:
            analysis = analyse_hand(profile, hand_record)
        except Exception as e:
            st.error(f"Hand saved successfully, but analysis failed: {e}")
            st.stop()

    # Step 4: Display analysis
    st.success("Hand saved.")
    st.divider()
    st.subheader(f"Analysis — {selected_player}")
    st.caption(f"Sample size: {profile['hand_count']} hand(s) | Confidence: {'Low' if profile['hand_count'] < 5 else 'Medium' if profile['hand_count'] < 15 else 'High'}")
    st.markdown(analysis)
