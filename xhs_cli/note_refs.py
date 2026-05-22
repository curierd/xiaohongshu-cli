"""Helpers for resolving and persisting note references across commands."""

from __future__ import annotations

import click

from .cookies import get_note_by_index, save_note_index
from .formatter import parse_note_reference


def resolve_note_reference(id_or_url: str, *, xsec_token: str = "") -> tuple[str, str, str]:
    """Resolve a note reference from URL/ID or the last listing index."""
    if id_or_url.isdigit():
        entry = get_note_by_index(int(id_or_url))
        if entry is None:
            raise click.UsageError(
                f"Index {id_or_url} not found — run a listing command first "
                "(search / feed / hot / user-posts / favorites / my-notes)"
            )
        return (
            entry["note_id"],
            xsec_token or entry.get("xsec_token", ""),
            entry.get("xsec_source", ""),
        )

    note_id, url_token, url_source = parse_note_reference(id_or_url)
    return note_id, xsec_token or url_token, url_source


def save_index_from_items(data: dict, *, xsec_source: str) -> None:
    """Persist ordered note references from list-style responses."""
    entries = []
    for item in data.get("items", []):
        note_card = item.get("note_card", {})
        note_id = item.get("id", note_card.get("note_id", ""))
        token = item.get("xsec_token", note_card.get("xsec_token", ""))
        if note_id:
            entries.append({
                "note_id": note_id,
                "xsec_token": token,
                "xsec_source": xsec_source if token else "",
            })
    save_note_index(entries)


def save_index_from_notes(notes: list[dict]) -> None:
    """Persist ordered note references from paged note payloads."""
    entries = []
    for note in notes:
        note_id = str(note.get("note_id", note.get("id", ""))).strip()
        if not note_id:
            continue
        # Only skip if title field explicitly exists and is empty (probably deleted note)
        # If title field doesn't exist, keep the note (could be test data or old API format)
        has_display_title = "display_title" in note
        title = note.get("display_title", "")[:40]
        if has_display_title and (not title or title.isspace()):
            continue
        entries.append({
            "note_id": note_id,
            "xsec_token": str(note.get("xsec_token", "")).strip(),
            "xsec_source": "",
        })
    save_note_index(entries)
