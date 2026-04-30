"""
Claude API client. Builds prompts, handles caching, parses responses.

Prompt caching strategy:
  - System prompt contains the player profile (cacheable — large, rarely changes).
  - User message contains the hand (not cached — unique per call).
"""

import streamlit as st
import anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024


@st.cache_resource
def _get_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_player_context(profile: dict) -> str:
    """
    Format a player profile into a readable system prompt block.
    This block is sent with cache_control so repeat calls against the same
    player in the same session hit the cache.
    """
    f = profile["fields"]
    tag_counts = profile["tag_counts"]
    hand_count = profile["hand_count"]

    # Format tag counts — only show tags with at least one occurrence
    if tag_counts:
        tag_lines = "\n".join(
            f"  {tag}: {count} time{'s' if count != 1 else ''}"
            for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])
        )
    else:
        tag_lines = "  (no tendency data recorded yet)"

    # Scouting report summary
    report_summary = "(no scouting report written yet)"
    if profile.get("scouting_report"):
        rf = profile["scouting_report"]["fields"]
        parts = []
        if rf.get("Primary Leak"):
            parts.append(f"Primary leak: {rf['Primary Leak']}")
        if rf.get("Secondary Leak"):
            parts.append(f"Secondary leak: {rf['Secondary Leak']}")
        if rf.get("Counter-Strategy"):
            parts.append(f"Counter-strategy: {rf['Counter-Strategy']}")
        if rf.get("Sizing Tell") and rf["Sizing Tell"] != "No":
            parts.append(f"Sizing tell: {rf['Sizing Tell']} — {rf.get('Sizing Tell Description', '')}")
        report_summary = "\n".join(parts) if parts else "(scouting report exists but fields are empty)"

    confidence = (
        "Low (< 5 hands — speculative)" if hand_count < 5
        else "Medium (5–14 hands)" if hand_count < 15
        else "High (15+ hands)"
    )

    return f"""You are a poker analysis assistant helping a live cash game player analyse their decisions against specific opponents.

PLAYER PROFILE: {f.get('Name', 'Unknown')}
Playing style: {f.get('Playing Style', 'Unknown')} | Threat level: {f.get('Threat Level', '?')}/5
Hands recorded: {hand_count} | Data confidence: {confidence}
Typical stake: {f.get('Typical Stake', 'Unknown')} | Venue: {f.get('Primary Venue', 'Unknown')}

OBSERVED TENDENCIES (from {hand_count} hands):
{tag_lines}

QUALITATIVE PROFILE:
Physical tells: {f.get('Physical Tells', 'None recorded')}
Tilt triggers: {f.get('Tilt Triggers', 'None recorded')}
Emotional profile: {f.get('Emotional Profile', 'None recorded')}
General notes: {f.get('General Notes', 'None recorded')}

SCOUTING REPORT:
{report_summary}

INSTRUCTIONS:
Analyse the hand the user describes. Focus on whether their action was optimal against THIS specific player based on the tendency data above. All recommendations must reference the observed patterns — do not give generic GTO advice that ignores who the opponent is. If data is sparse (< 5 hands), note that your advice is speculative.

Format your response exactly as:
VERDICT: [Optimal / Suboptimal / Situational] — [one sentence]

ALTERNATIVES:
① [action]: [reasoning citing specific tags and counts]
② [action if applicable]: [reasoning]

EXPLOIT ADJUSTMENT:
[one concrete takeaway for future hands vs. this player]"""


def build_hand_context(hand_data: dict) -> str:
    """Format a submitted hand into the user message."""
    lines = [
        "HAND TO ANALYSE:",
        f"Date: {hand_data.get('Date', '?')} | Venue: {hand_data.get('Venue', '?')} | Stakes: {hand_data.get('Stakes', '?')}",
        f"Hero position: {hand_data.get('Hero Position', '?')} | Villain position: {hand_data.get('Villain Position', '?')}",
        f"Street of key action: {hand_data.get('Street of Key Action', '?')}",
        f"Key decision summary: {hand_data.get('Key Decision Summary', '?')}",
        f"Hero's action: {hand_data.get('Your Action', '?')}",
        f"Pot size: ${hand_data.get('Pot Size', '?')}",
        f"Result: {hand_data.get('Result', '?')}",
        f"Tags applied: {', '.join(hand_data.get('Tendency Tags', []) or ['none'])}",
        f"Notes: {hand_data.get('Notes', '')}",
    ]

    if hand_data.get("Entry Mode") == "Detailed":
        lines.append("")
        lines.append("FULL HAND DETAIL:")
        if hand_data.get("Hero Hole Cards"):
            lines.append(f"Hero cards: {hand_data['Hero Hole Cards']}")
        if hand_data.get("Villain Hole Cards"):
            lines.append(f"Villain cards: {hand_data['Villain Hole Cards']}")
        if hand_data.get("Effective Stack"):
            lines.append(f"Effective stack: ${hand_data['Effective Stack']}")
        if hand_data.get("Preflop Action"):
            lines.append(f"Preflop: {hand_data['Preflop Action']}")
        if hand_data.get("Flop"):
            lines.append(f"Flop ({hand_data['Flop']}): {hand_data.get('Flop Action', '')}")
        if hand_data.get("Turn"):
            lines.append(f"Turn ({hand_data['Turn']}): {hand_data.get('Turn Action', '')}")
        if hand_data.get("River"):
            lines.append(f"River ({hand_data['River']}): {hand_data.get('River Action', '')}")
        if hand_data.get("Showdown"):
            lines.append(f"Showdown: {hand_data['Showdown']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyse_hand(profile: dict, hand_data: dict) -> str:
    """
    Call Claude with the player profile (cached) + hand context.
    Returns the raw analysis text.
    """
    client = _get_client()
    system_text = build_player_context(profile)
    user_text = build_hand_context(hand_data)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_text}],
    )
    return response.content[0].text


def generate_scouting_report_draft(profile: dict) -> str:
    """
    Generate a draft scouting report from a player's hand history.
    Used on the Scouting Reports page.
    """
    client = _get_client()
    hand_count = profile["hand_count"]
    tag_counts = profile["tag_counts"]
    f = profile["fields"]

    tag_summary = "\n".join(
        f"  {tag}: {count}" for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])
    ) or "  No tags recorded."

    prompt = f"""You are writing a poker scouting report for a live cash game player to use against a specific opponent.

PLAYER: {f.get('Name', 'Unknown')}
Style: {f.get('Playing Style', 'Unknown')} | Threat: {f.get('Threat Level', '?')}/5
Hands recorded: {hand_count}

TENDENCY TAG COUNTS:
{tag_summary}

QUALITATIVE NOTES:
Physical tells: {f.get('Physical Tells', 'None')}
Tilt triggers: {f.get('Tilt Triggers', 'None')}
Emotional profile: {f.get('Emotional Profile', 'None')}
General notes: {f.get('General Notes', 'None')}

Write a concise scouting report. Format exactly as:

PRIMARY LEAK:
[The single most exploitable pattern]

SECONDARY LEAK:
[Second-most exploitable pattern]

SIZING TELL:
[Yes / No / Suspected — describe the specific sizing pattern if present]

COUNTER-STRATEGY:
[How to adjust overall strategy vs. this player]

PREFLOP ADJUSTMENT:
[Specific preflop change, e.g. "3-bet wider for value, avoid bluff 3-bets"]

POSTFLOP ADJUSTMENT:
[Specific postflop change, e.g. "cbet every flop, give up turn vs. calls"]

AVOID:
[What NOT to do vs. this player]

Note: sample size is {hand_count} hands. Flag any low-confidence observations."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
