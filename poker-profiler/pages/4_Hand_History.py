"""
Page 4 — Hand History
Review, edit, and delete recorded hands per player.
"""

import streamlit as st
from utils.tag_definitions import TENDENCY_TAGS, POSITIONS, STREETS, RESULTS
from utils.airtable_client import get_all_players, get_hand_history, delete_hand_record, update_hand_record

st.set_page_config(page_title="Hand History — Poker Profiler", page_icon="📖", layout="centered")
st.title("📖 Hand History")
st.caption("Review, edit, or delete hands recorded against a specific player.")

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
    record_id = hand["id"]
    entry_mode = f.get("Entry Mode", "Quick")
    hand_date = f.get("Date", "No date")
    street = f.get("Street of Key Action", "?")
    summary = f.get("Key Decision Summary", "No summary")
    result = f.get("Result", "?")
    tags = f.get("Tendency Tags", [])

    label = f"[{hand_date}] {street} — {summary[:60]}{'...' if len(summary) > 60 else ''}  |  {result}"
    if entry_mode == "Detailed":
        label = "🔍 " + label

    with st.expander(label):

        edit_key = f"edit_{record_id}"
        confirm_key = f"confirm_delete_{record_id}"

        # ---------------------------------------------------------------
        # View mode
        # ---------------------------------------------------------------
        if not st.session_state.get(edit_key):
            col1, col2, col3 = st.columns(3)
            col1.metric("Date", hand_date)
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

            st.divider()
            col_edit, col_del = st.columns(2)

            if col_edit.button("✏️ Edit", key=f"editbtn_{record_id}"):
                st.session_state[edit_key] = True
                st.rerun()

            if st.session_state.get(confirm_key):
                st.warning("Are you sure? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                if col_yes.button("Yes, delete", key=f"yes_{record_id}", type="primary"):
                    try:
                        delete_hand_record(record_id)
                        st.success("Hand deleted.")
                        st.session_state[confirm_key] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
                if col_no.button("Cancel", key=f"no_{record_id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if col_del.button("🗑 Delete", key=f"delete_{record_id}"):
                    st.session_state[confirm_key] = True
                    st.rerun()

        # ---------------------------------------------------------------
        # Edit mode
        # ---------------------------------------------------------------
        else:
            st.markdown("**Editing hand**")

            with st.form(f"edit_form_{record_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_venue = st.text_input("Venue", value=f.get("Venue", ""))
                with col2:
                    new_stakes = st.text_input("Stakes", value=f.get("Stakes", ""))

                col3, col4 = st.columns(2)
                with col3:
                    new_hero_pos = st.selectbox("Your Position", POSITIONS,
                        index=POSITIONS.index(f["Hero Position"]) if f.get("Hero Position") in POSITIONS else 0)
                with col4:
                    new_villain_pos = st.selectbox("Villain Position", POSITIONS,
                        index=POSITIONS.index(f["Villain Position"]) if f.get("Villain Position") in POSITIONS else 0)

                new_street = st.selectbox("Street of Key Action", STREETS,
                    index=STREETS.index(f["Street of Key Action"]) if f.get("Street of Key Action") in STREETS else 0)
                new_summary = st.text_area("Key Decision Summary", value=f.get("Key Decision Summary", ""), height=80)
                new_action = st.text_area("Your Action", value=f.get("Your Action", ""), height=68)

                col5, col6 = st.columns(2)
                with col5:
                    new_pot = st.number_input("Pot Size ($)", value=float(f.get("Pot Size", 0) or 0), min_value=0.0, step=5.0)
                with col6:
                    new_result = st.selectbox("Result", RESULTS,
                        index=RESULTS.index(f["Result"]) if f.get("Result") in RESULTS else 0)

                st.markdown("**Tendency Tags**")
                new_tags = []
                for category, tag_list in TENDENCY_TAGS.items():
                    with st.expander(category):
                        cols = st.columns(2)
                        for i, tag in enumerate(tag_list):
                            if cols[i % 2].checkbox(tag, value=(tag in tags), key=f"etag_{record_id}_{tag}"):
                                new_tags.append(tag)

                new_notes = st.text_area("Notes", value=f.get("Notes", ""), height=100)

                if entry_mode == "Detailed":
                    st.divider()
                    st.markdown("**Full Hand Detail**")
                    new_hero_cards = st.text_input("Your Hole Cards", value=f.get("Hero Hole Cards", ""))
                    new_villain_cards = st.text_input("Villain Hole Cards", value=f.get("Villain Hole Cards", ""))
                    new_stack = st.number_input("Effective Stack ($)", value=float(f.get("Effective Stack", 0) or 0), min_value=0.0, step=5.0)
                    new_preflop = st.text_area("Preflop Action", value=f.get("Preflop Action", ""), height=68)
                    col7, col8 = st.columns([1, 3])
                    with col7:
                        new_flop = st.text_input("Flop", value=f.get("Flop", ""))
                    with col8:
                        new_flop_action = st.text_area("Flop Action", value=f.get("Flop Action", ""), height=68)
                    col9, col10 = st.columns([1, 3])
                    with col9:
                        new_turn = st.text_input("Turn", value=f.get("Turn", ""))
                    with col10:
                        new_turn_action = st.text_area("Turn Action", value=f.get("Turn Action", ""), height=68)
                    col11, col12 = st.columns([1, 3])
                    with col11:
                        new_river = st.text_input("River", value=f.get("River", ""))
                    with col12:
                        new_river_action = st.text_area("River Action", value=f.get("River Action", ""), height=68)
                    new_showdown = st.text_area("Showdown", value=f.get("Showdown", ""), height=68)

                col_save, col_cancel = st.columns(2)
                save = col_save.form_submit_button("💾 Save Changes", type="primary")
                cancel = col_cancel.form_submit_button("Cancel")

            if save:
                updated = {
                    "Venue": new_venue,
                    "Stakes": new_stakes,
                    "Hero Position": new_hero_pos,
                    "Villain Position": new_villain_pos,
                    "Street of Key Action": new_street,
                    "Key Decision Summary": new_summary.strip(),
                    "Your Action": new_action.strip(),
                    "Pot Size": new_pot,
                    "Result": new_result,
                    "Tendency Tags": new_tags,
                    "Notes": new_notes.strip(),
                }
                if entry_mode == "Detailed":
                    updated.update({
                        "Hero Hole Cards": new_hero_cards,
                        "Villain Hole Cards": new_villain_cards,
                        "Effective Stack": new_stack,
                        "Preflop Action": new_preflop,
                        "Flop": new_flop,
                        "Flop Action": new_flop_action,
                        "Turn": new_turn,
                        "Turn Action": new_turn_action,
                        "River": new_river,
                        "River Action": new_river_action,
                        "Showdown": new_showdown,
                    })
                try:
                    update_hand_record(record_id, updated)
                    st.success("Hand updated.")
                    st.session_state[edit_key] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

            if cancel:
                st.session_state[edit_key] = False
                st.rerun()
