"""
Page 3 — Scouting Reports
View, generate, edit, and save per-player scouting reports.
"""

import streamlit as st
from datetime import date

from utils.airtable_client import get_all_players, get_player_profile, save_scouting_report
from utils.claude_client import generate_scouting_report_draft

st.set_page_config(page_title="Scouting Reports — Poker Profiler", page_icon="📋", layout="centered")
st.title("📋 Scouting Reports")
st.caption("One-page exploitative profiles per player. Generate a draft from hand data, then review and save.")

# ---------------------------------------------------------------------------
# Load players
# ---------------------------------------------------------------------------
try:
    players = get_all_players()
except Exception as e:
    st.error(f"Could not connect to Airtable: {e}")
    st.stop()

if not players:
    st.info("No players yet. Add players on the Player Profiles page.")
    st.stop()

# ---------------------------------------------------------------------------
# Player selector
# ---------------------------------------------------------------------------
player_names = [p["name"] for p in players]
player_map = {p["name"]: p["id"] for p in players}

selected_name = st.selectbox("Select player", player_names)
player_id = player_map[selected_name]

try:
    profile = get_player_profile(player_id)
except Exception as e:
    st.error(f"Could not load player profile: {e}")
    st.stop()

hand_count = profile["hand_count"]
tag_counts = profile["tag_counts"]
existing_report = profile.get("scouting_report")

# Hand count status
if hand_count < 5:
    st.warning(
        f"⚠ Only {hand_count} hand(s) recorded for {selected_name}. "
        "Scouting reports are unreliable with fewer than 5 hands. Record more hands first."
    )
elif hand_count < 15:
    st.info(f"{hand_count} hands recorded. Moderate data — report will have some uncertainty.")
else:
    st.success(f"{hand_count} hands recorded. Good data for a reliable report.")

st.divider()

# ---------------------------------------------------------------------------
# Existing report display
# ---------------------------------------------------------------------------
if existing_report:
    rf = existing_report["fields"]
    st.subheader(f"Current Report — {selected_name}")
    st.caption(f"Last updated: {rf.get('Last Updated', '?')} | Sample: {rf.get('Sample Size', '?')} hands | Confidence: {rf.get('Confidence Rating', '?')}/5")

    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"**Primary Leak:** {rf.get('Primary Leak', '—')}")
        st.markdown(f"**Secondary Leak:** {rf.get('Secondary Leak', '—')}")
        st.markdown(f"**Sizing Tell:** {rf.get('Sizing Tell', '—')}")
        if rf.get("Sizing Tell Description"):
            st.caption(rf["Sizing Tell Description"])
    with cols[1]:
        st.markdown(f"**Preflop Adjustment:** {rf.get('Preflop Adjustment', '—')}")
        st.markdown(f"**Postflop Adjustment:** {rf.get('Postflop Adjustment', '—')}")
        st.markdown(f"**Avoid:** {rf.get('Avoid', '—')}")

    st.markdown(f"**Counter-Strategy:** {rf.get('Counter-Strategy', '—')}")
    st.divider()

# ---------------------------------------------------------------------------
# Generate draft
# ---------------------------------------------------------------------------
st.subheader("Generate / Regenerate Draft")

if st.button("🤖 Generate Draft from Hand Data", disabled=hand_count == 0, type="primary"):
    with st.spinner(f"Generating report for {selected_name} from {hand_count} hands..."):
        try:
            draft = generate_scouting_report_draft(profile)
            st.session_state[f"draft_{player_id}"] = draft
        except Exception as e:
            st.error(f"Failed to generate draft: {e}")

# Show draft if available
draft_key = f"draft_{player_id}"
if draft_key in st.session_state:
    st.markdown("**Draft (review before saving):**")
    st.text(st.session_state[draft_key])
    st.caption("Copy the sections you want to keep into the form below, then save.")
    st.divider()

# ---------------------------------------------------------------------------
# Edit and save form
# ---------------------------------------------------------------------------
st.subheader("Save Report")

pre = existing_report["fields"] if existing_report else {}

with st.form("scouting_report_form"):
    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.number_input("Sample Size (hands)", value=hand_count, min_value=0)
    with col2:
        confidence = st.slider("Confidence Rating", 1, 5, pre.get("Confidence Rating", 2))

    primary_leak = st.text_area("Primary Leak *", value=pre.get("Primary Leak", ""), height=80,
                                 placeholder="The single most exploitable pattern.")
    secondary_leak = st.text_area("Secondary Leak", value=pre.get("Secondary Leak", ""), height=80,
                                   placeholder="Second-most exploitable pattern.")

    sizing_tell = st.selectbox("Sizing Tell", ["No", "Suspected", "Yes"],
                                index=["No", "Suspected", "Yes"].index(pre.get("Sizing Tell", "No")) if pre.get("Sizing Tell") in ["No", "Suspected", "Yes"] else 0)
    sizing_tell_desc = st.text_input("Sizing Tell Description", value=pre.get("Sizing Tell Description", ""),
                                      placeholder="e.g. Overbets river as bluff, min-bets sets.")

    counter_strategy = st.text_area("Counter-Strategy", value=pre.get("Counter-Strategy", ""), height=80,
                                     placeholder="Overall adjustment vs. this player.")
    preflop_adj = st.text_area("Preflop Adjustment", value=pre.get("Preflop Adjustment", ""), height=68,
                                placeholder="e.g. 3-bet wider for value, skip bluff 3-bets.")
    postflop_adj = st.text_area("Postflop Adjustment", value=pre.get("Postflop Adjustment", ""), height=68,
                                 placeholder="e.g. Cbet every flop, give up turn vs. calls.")
    avoid = st.text_area("Avoid", value=pre.get("Avoid", ""), height=68,
                          placeholder="What NOT to do vs. this player.")

    if st.form_submit_button("💾 Save Report", type="primary"):
        if not primary_leak.strip():
            st.error("Primary Leak is required.")
        else:
            try:
                save_scouting_report(player_id, {
                    "Sample Size": sample_size,
                    "Confidence Rating": confidence,
                    "Primary Leak": primary_leak.strip(),
                    "Secondary Leak": secondary_leak.strip() or None,
                    "Sizing Tell": sizing_tell,
                    "Sizing Tell Description": sizing_tell_desc.strip() or None,
                    "Counter-Strategy": counter_strategy.strip() or None,
                    "Preflop Adjustment": preflop_adj.strip() or None,
                    "Postflop Adjustment": postflop_adj.strip() or None,
                    "Avoid": avoid.strip() or None,
                    "Date Authored": date.today().isoformat(),
                })
                st.success(f"Scouting report saved for {selected_name}.")
                if draft_key in st.session_state:
                    del st.session_state[draft_key]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save report: {e}")
