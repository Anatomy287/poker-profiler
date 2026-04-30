"""
Page 2 — Player Profiles
View all players, add new players, write notes and session notes.
"""

import streamlit as st
from datetime import date

from utils.tag_definitions import PLAYING_STYLES, PRIORITY_TAGS, TAG_DESCRIPTIONS
from utils.airtable_client import get_all_players, get_player_profile, create_player, update_player_notes

st.set_page_config(page_title="Player Profiles — Poker Profiler", page_icon="👤", layout="centered")
st.title("👤 Player Profiles")

# ---------------------------------------------------------------------------
# Load players
# ---------------------------------------------------------------------------
try:
    players = get_all_players()
except Exception as e:
    st.error(f"Could not connect to Airtable: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Add New Player
# ---------------------------------------------------------------------------
with st.expander("➕ Add New Player", expanded=not players):
    with st.form("add_player_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name / Alias *", placeholder="e.g. Tony the Fish")
            new_venue = st.text_input("Primary Venue", placeholder="e.g. Crown Casino")
        with col2:
            new_stake = st.text_input("Typical Stake", placeholder="e.g. $1/$2 NLH")
            new_style = st.selectbox("Playing Style", PLAYING_STYLES)

        new_threat = st.slider("Threat Level", 1, 5, 2, help="1 = easy fish, 5 = dangerous reg")
        new_first_seen = st.date_input("Date First Encountered", value=date.today())
        new_notes = st.text_area("Initial Notes", placeholder="First impressions, tells, anything notable.", height=80)

        if st.form_submit_button("Add Player", type="primary"):
            if not new_name.strip():
                st.error("Name is required.")
            else:
                try:
                    create_player({
                        "Name": new_name.strip(),
                        "Primary Venue": new_venue,
                        "Typical Stake": new_stake,
                        "Playing Style": new_style,
                        "Threat Level": new_threat,
                        "Date First Encountered": new_first_seen.isoformat(),
                        "General Notes": new_notes.strip() or None,
                    })
                    st.success(f"Player '{new_name.strip()}' added.")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create player: {e}")

st.divider()

# ---------------------------------------------------------------------------
# Player list
# ---------------------------------------------------------------------------
if not players:
    st.info("No players yet. Add one above.")
    st.stop()

st.subheader(f"{len(players)} Player{'s' if len(players) != 1 else ''}")

for player in players:
    with st.expander(player["name"]):
        try:
            profile = get_player_profile(player["id"])
        except Exception as e:
            st.error(f"Could not load profile: {e}")
            continue

        f = profile["fields"]
        tag_counts = profile["tag_counts"]
        hand_count = profile["hand_count"]

        # --- Summary row ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Hands", hand_count)
        col2.metric("Style", f.get("Playing Style", "Unknown"))
        col3.metric("Threat", f"{f.get('Threat Level', '?')}/5")
        col4.metric("Venue", f.get("Primary Venue", "—"))

        if f.get("Typical Stake"):
            st.caption(f"Stake: {f['Typical Stake']}")
        if f.get("Date First Encountered"):
            st.caption(f"First seen: {f['Date First Encountered']} | Last seen: {f.get('Last Session Seen', 'not recorded')}")

        # --- Priority tendency counts ---
        if tag_counts:
            st.markdown("**Tendency Counts**")
            priority_found = {t: tag_counts[t] for t in PRIORITY_TAGS if t in tag_counts}
            other = {t: c for t, c in tag_counts.items() if t not in PRIORITY_TAGS}

            if priority_found:
                cols = st.columns(3)
                for i, (tag, count) in enumerate(priority_found.items()):
                    cols[i % 3].metric(tag, count)

            if other:
                with st.expander("All other tags"):
                    for tag, count in sorted(other.items(), key=lambda x: -x[1]):
                        st.write(f"• {tag}: **{count}**  — {TAG_DESCRIPTIONS.get(tag, '')}")

        # --- Qualitative profile ---
        with st.expander("Qualitative Profile"):
            st.write(f"**Physical Tells:** {f.get('Physical Tells', 'None recorded')}")
            st.write(f"**Tilt Triggers:** {f.get('Tilt Triggers', 'None recorded')}")
            st.write(f"**Emotional Profile:** {f.get('Emotional Profile', 'None recorded')}")

        st.divider()

        # --- General Notes ---
        st.markdown("**General Notes** *(evergreen observations — editable)*")
        general_notes_val = f.get("General Notes", "") or ""
        new_general = st.text_area(
            "General Notes",
            value=general_notes_val,
            height=120,
            label_visibility="collapsed",
            key=f"general_notes_{player['id']}",
            placeholder="Physical tells, seat preferences, habits, anything that doesn't change much.",
        )
        if st.button("Save General Notes", key=f"save_general_{player['id']}"):
            try:
                update_player_notes(player["id"], general_notes=new_general, new_session_note=None)
                st.success("General notes saved.")
            except Exception as e:
                st.error(f"Failed to save: {e}")

        st.divider()

        # --- Session Notes ---
        st.markdown("**Session Notes** *(running log — entries are never overwritten)*")
        new_session_note = st.text_area(
            "New session note",
            height=68,
            key=f"session_input_{player['id']}",
            placeholder="e.g. Seemed tilted after a bad beat in hour 2. Played much looser.",
        )
        if st.button("Add Session Note", key=f"add_session_{player['id']}"):
            if not new_session_note.strip():
                st.warning("Type a note before adding.")
            else:
                try:
                    update_player_notes(player["id"], general_notes=None, new_session_note=new_session_note.strip())
                    st.success("Session note added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

        existing_session = f.get("Session Notes", "") or ""
        if existing_session:
            st.markdown("*Previous entries:*")
            st.text(existing_session)
        else:
            st.caption("No session notes yet.")

        # --- Linked scouting report ---
        if profile.get("scouting_report"):
            rf = profile["scouting_report"]["fields"]
            with st.expander("📋 Scouting Report", expanded=False):
                st.caption(f"Last updated: {rf.get('Last Updated', 'unknown')} | Sample: {rf.get('Sample Size', '?')} hands | Confidence: {rf.get('Confidence Rating', '?')}/5")
                if rf.get("Primary Leak"):
                    st.markdown(f"**Primary Leak:** {rf['Primary Leak']}")
                if rf.get("Secondary Leak"):
                    st.markdown(f"**Secondary Leak:** {rf['Secondary Leak']}")
                if rf.get("Counter-Strategy"):
                    st.markdown(f"**Counter-Strategy:** {rf['Counter-Strategy']}")
                if rf.get("Avoid"):
                    st.markdown(f"**Avoid:** {rf['Avoid']}")
                st.info("Edit the full report on the Scouting Reports page.")
        else:
            st.caption("No scouting report yet. Generate one on the Scouting Reports page once you have 5+ hands.")
