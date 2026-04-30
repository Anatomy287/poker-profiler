from datetime import date
  import streamlit as st
  from pyairtable import Api


  @st.cache_resource
  def _get_api():
      return Api(st.secrets["AIRTABLE_TOKEN"])


  def _table(name: str):
      api = _get_api()
      return api.table(st.secrets["AIRTABLE_BASE_ID"], name)


  def get_all_players() -> list[dict]:
      records = _table("Players").all(fields=["Name"])
      return sorted(
          [{"id": r["id"], "name": r["fields"].get("Name", "Unnamed")} for r in records],
          key=lambda x: x["name"].lower(),
      )


  def get_player_profile(player_id: str) -> dict:
      player = _table("Players").get(player_id)
      fields = player["fields"]

      all_hands = _table("Hand Histories").all()
      hands = [h for h in all_hands if player_id in h["fields"].get("Player", [])]

      tag_counts: dict[str, int] = {}
      for hand in hands:
          for tag in hand["fields"].get("Tendency Tags", []):
              tag_counts[tag] = tag_counts.get(tag, 0) + 1

      scouting_report = None
      report_ids = fields.get("Scouting Reports", [])
      if report_ids:
          try:
              scouting_report = _table("Scouting Reports").get(report_ids[0])
          except Exception:
              pass

      return {
          "id": player_id,
          "fields": fields,
          "hand_count": len(hands),
          "tag_counts": tag_counts,
          "hands": hands,
          "scouting_report": scouting_report,
      }


  def create_player(player_data: dict) -> str:
      record = _table("Players").create(player_data)
      return record["id"]


  def update_player_notes(player_id: str, general_notes: str | None, new_session_note: str | None) -> None:
      updates: dict = {}

      if general_notes is not None:
          updates["General Notes"] = general_notes

      if new_session_note and new_session_note.strip():
          existing = _table("Players").get(player_id)["fields"].get("Session Notes", "") or ""
          dated_entry = f"[{date.today().isoformat()}] {new_session_note.strip()}"
          updates["Session Notes"] = dated_entry + ("\n" + existing if existing else "")

      if updates:
          _table("Players").update(player_id, updates)


  def save_hand_record(hand_data: dict) -> str:
      record = _table("Hand Histories").create(hand_data)
      return record["id"]


  def get_hand_history(player_id: str) -> list[dict]:
      all_hands = _table("Hand Histories").all(sort=[{"field": "Date", "direction": "desc"}])
      return [h for h in all_hands if player_id in h["fields"].get("Player", [])]


  def save_scouting_report(player_id: str, report_data: dict) -> str:
      player = _table("Players").get(player_id)
      existing_ids = player["fields"].get("Scouting Reports", [])

      report_data["Player"] = [player_id]
      report_data["Last Updated"] = date.today().isoformat()

      if existing_ids:
          _table("Scouting Reports").update(existing_ids[0], report_data)
          return existing_ids[0]
      else:
          record = _table("Scouting Reports").create(report_data)
          return record["id"]
