"""
Page 4 — Hand History
Review all recorded hands for a player, newest first.
"""

import streamlit as st
from utils.airtable_client import get_all_players, get_hand_history

st.set_page_config(page_title="Hand History — Poker Profiler", page_icon="📖", layout="centered")
st.title("📖 Hand History")
st.caption("Review all hands recorded against a specific player.")

try:
    players = get_all_players()
except Exception as e:
    st.error(f"Could not connect to Airtable: {e}")
    st.stop()

if not players:
    st.info("No players yet. Add one on the Player Profiles page.")
    st.stop()

player_names = [p["name"] for p in players]
player_map = {p["name"]: p["id"] for p in players}

selected_name = st.selectbox("Select player", player_names)
player_id = player_map[selected_name]

try:
    hands = get_hand_history(player_id)
except Exception as e:
    st.error(f"Could not load hands: {e}")
    st.stop()

st.divider()

if not hands:
    st.info(f"No hands recorded for {selected_name} yet.")
    st.stop()

st.subheader(f"{len(hands)} hand{'s' if len(hands) != 1 else ''} — {selected_name}")

for hand in hands:
    f = hand["fields"]
    entry_mode = f.get("Entry Mode", "Quick")
    date = f.get("Date", "No date")
    street = f.get("Street of Key Action", "?")
    summary = f.get("Key Decision Summary", "No summary")
    result = f.get("Result", "?")
    tags = f.get("Tendency Tags", [])

    label = f"[{date}] {street} — {summary[:60]}{'...' if len(summary) > 60 else ''}  |  {result}"
    if entry_mode == "Detailed":
        label = "🔍 " + label

    with st.expander(label):
        col1, col2, col3 = st.columns(3)
        col1.metric("Date", date)
        col2.metric("Result", result)
        col3.metric("Pot", f"${f.get('Pot Size', '?')}")

        col4, col5 = st.columns(2)
        col4.write(f"**Hero Position:** {f.get('Hero Position', '?')}")
        col5.write(f"**Villain Position:** {f.get('Villain Position', '?')}")

        st.write(f"**Venue:** {f.get('Venue', '—')}  |  **Stakes:** {f.get('Stakes', '—')}")
        st.write(f"**Street:** {street}")
        st.write(f"**Key Decision:** {summary}")
        st.write(f"**Your Action:** {f.get('Your Action', '—')}")

        if tags:
            st.write(f"**Tags:** {', '.join(tags)}")

        if f.get("Notes"):
            st.write(f"**Notes:** {f['Notes']}")

        if entry_mode == "Detailed":
            st.divider()
            st.markdown("**Full Hand Detail**")

            if f.get("Hero Hole Cards"):
                st.write(f"Hero: {f['Hero Hole Cards']}  |  Villain: {f.get('Villain Hole Cards', '—')}")
            if f.get("Effective Stack"):
                st.write(f"Effective stack: ${f['Effective Stack']}")
            if f.get("Preflop Action"):
                st.write(f"**Preflop:** {f['Preflop Action']}")
            if f.get("Flop"):
                st.write(f"**Flop ({f['Flop']}):** {f.get('Flop Action', '—')}")
            if f.get("Turn"):
                st.write(f"**Turn ({f['Turn']}):** {f.get('Turn Action', '—')}")
            if f.get("River"):
                st.write(f"**River ({f['River']}):** {f.get('River Action', '—')}")
            if f.get("Showdown"):
                st.write(f"**Showdown:** {f['Showdown']}")
