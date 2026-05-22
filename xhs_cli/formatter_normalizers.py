"""Normalize reverse-engineered API payloads into stable renderer-friendly shapes."""

from __future__ import annotations

from typing import Any


def _coerce_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def normalize_user_info(data: dict[str, Any]) -> dict[str, Any]:
    basic = data.get("basic_info", data)
    interactions = data.get("interactions", [])

    stats = {}
    for item in interactions:
        stats[item.get("type", "")] = item.get("count", "0")

    return {
        "nickname": basic.get("nickname", basic.get("nick_name", "Unknown")),
        "red_id": basic.get("red_id", ""),
        "desc": basic.get("desc", ""),
        "ip_location": basic.get("ip_location", ""),
        "user_id": basic.get("user_id", data.get("user_id", "")),
        "gender": basic.get("gender"),
        "stats": stats,
    }


def normalize_note_detail(data: dict[str, Any]) -> dict[str, Any] | None:
    items = data.get("items", [])
    if not items:
        return None

    item = items[0]
    note = item.get("note_card", item.get("note", {}))
    user = note.get("user", {})
    interact = note.get("interact_info", {})
    tags = note.get("tag_list", [])

    # Try to get time from multiple locations
    time_val = (
        note.get("time")
        or note.get("timestamp")
        or note.get("create_time")
        or note.get("ctime")
        or item.get("time")
        or item.get("timestamp")
        or item.get("create_time")
        or item.get("ctime")
    )

    return {
        "title": note.get("title", note.get("display_title", "Untitled")),
        "desc": note.get("desc", ""),
        "author": user.get("nickname", "Unknown"),
        "liked_count": interact.get("liked_count", "0"),
        "collected_count": interact.get("collected_count", "0"),
        "comment_count": interact.get("comment_count", "0"),
        "share_count": interact.get("share_count", "0"),
        "tags": [tag.get("name", "") for tag in tags if tag.get("name")],
        "image_count": len(note.get("image_list", [])),
        "time": time_val,
    }


def normalize_note_summary(item: dict[str, Any]) -> dict[str, Any] | None:
    # Skip items that are not notes
    model_type = item.get("model_type")
    if model_type and model_type != "note":
        return None

    note_card = item.get("note_card", item)
    if not isinstance(note_card, dict):
        return None

    # If there's no note_card but the item itself doesn't look like a note, skip it
    if "note_card" not in item and "title" not in note_card and "display_title" not in note_card:
        return None

    # Check if title field exists and get its value
    has_title = "title" in note_card
    has_display_title = "display_title" in note_card
    title = str(note_card.get("title", note_card.get("display_title", "")))[:40]

    # Skip if title field explicitly exists and is empty (probably deleted note)
    # Also skip if both title fields don't exist and title is empty
    if (has_title or has_display_title) and (not title or title.isspace()):
        return None
    if not (has_title or has_display_title) and (not title or title.isspace()):
        return None

    user = note_card.get("user", {})
    interact = note_card.get("interact_info", {})

    # Extract relative time from corner_tag_info if available
    time_str = None
    corner_tags = note_card.get("corner_tag_info", [])
    for tag in corner_tags:
        if isinstance(tag, dict) and tag.get("type") == "publish_time":
            time_str = tag.get("text")
            break

    return {
        "title": title,
        "author": user.get("nickname", ""),
        "liked": str(interact.get("liked_count", "")),
        "note_type": "video" if note_card.get("type") == "video" else "image",
        "note_id": item.get("id", note_card.get("note_id", "")),
        "xsec_token": item.get("xsec_token", note_card.get("xsec_token", "")),
        "time": (
            note_card.get("time")
            or note_card.get("timestamp")
            or note_card.get("create_time")
            or note_card.get("ctime")
        ),
        "time_str": time_str,
    }


def normalize_search_results(data: dict[str, Any]) -> dict[str, Any]:
    items = [item for item in (normalize_note_summary(item) for item in data.get("items", [])) if item]
    return {
        "items": items,
        "has_more": bool(data.get("has_more", False)),
    }


def normalize_comments(data: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for comment in data.get("comments", []):
        user = comment.get("user_info", {})
        normalized.append({
            "nickname": user.get("nickname", "Unknown"),
            "content": comment.get("content", ""),
            "like_count": comment.get("like_count", "0"),
            "sub_comment_count": _coerce_int(comment.get("sub_comment_count", 0)),
            "time": (
                comment.get("time")
                or comment.get("timestamp")
                or comment.get("create_time")
                or comment.get("ctime")
            ),
        })
    return normalized


def normalize_feed(data: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for item in data.get("items", [])[:20]:
        # Skip items that are not notes
        model_type = item.get("model_type")
        if model_type and model_type != "note":
            continue

        note_card = item.get("note_card", {})

        # Skip if there's no note_card and no title fields
        if "note_card" not in item and "title" not in note_card and "display_title" not in note_card:
            continue

        # Check if title field exists and get its value
        has_title = "title" in note_card
        has_display_title = "display_title" in note_card
        title = note_card.get("title", note_card.get("display_title", ""))[:40]

        # Skip if title field explicitly exists and is empty (probably deleted note)
        # Also skip if both title fields don't exist and title is empty
        if (has_title or has_display_title) and (not title or title.isspace()):
            continue
        if not (has_title or has_display_title) and (not title or title.isspace()):
            continue

        user = note_card.get("user", {})
        interact = note_card.get("interact_info", {})

        # Extract relative time from corner_tag_info if available
        time_str = None
        corner_tags = note_card.get("corner_tag_info", [])
        for tag in corner_tags:
            if isinstance(tag, dict) and tag.get("type") == "publish_time":
                time_str = tag.get("text")
                break

        normalized.append({
            "title": title,
            "author": user.get("nickname", ""),
            "liked": str(interact.get("liked_count", "")),
            "note_id": item.get("id", ""),
            "xsec_token": item.get("xsec_token", note_card.get("xsec_token", "")),
            "time": (
                note_card.get("time")
                or note_card.get("timestamp")
                or note_card.get("create_time")
                or note_card.get("ctime")
            ),
            "time_str": time_str,
        })
    return normalized


def normalize_user_posts(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for note in notes:
        # Check if title field exists and get its value
        has_display_title = "display_title" in note
        title = note.get("display_title", "")[:40]

        # Only skip if title field explicitly exists and is empty (probably deleted note)
        # If title field doesn't exist, keep the note (could be test data or old API format)
        if has_display_title and (not title or title.isspace()):
            continue

        interact = note.get("interact_info", {})
        normalized.append({
            "title": title,
            "liked": str(interact.get("liked_count", note.get("liked_count", ""))),
            "note_type": "video" if note.get("type") == "video" else "image",
            "note_id": note.get("note_id", ""),
            "time": (
                note.get("time")
                or note.get("timestamp")
                or note.get("create_time")
                or note.get("ctime")
            ),
        })
    return normalized


def normalize_topics(data: Any) -> list[dict[str, Any]]:
    topics = data if isinstance(data, list) else data.get("topic_info_dtos", [])
    return [
        {
            "name": topic.get("name", ""),
            "view_num": topic.get("view_num", 0),
            "topic_id": topic.get("id", ""),
        }
        for topic in topics
    ]


def normalize_users(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        users = data
    elif isinstance(data, dict):
        users = data.get("user_info_dtos") or data.get("users") or data.get("items") or []
    else:
        users = []

    normalized = []
    for user in users:
        base = user.get("user_base_dto", user)
        normalized.append({
            "nickname": base.get("user_nickname", base.get("nickname", base.get("nick_name", ""))),
            "red_id": base.get("red_id", ""),
            "fans": user.get("fans_total", base.get("fans", base.get("fansCount", 0))),
            "user_id": base.get("user_id", base.get("id", "")),
        })
    return normalized


def normalize_creator_notes(data: Any) -> list[dict[str, Any]]:
    notes = data if isinstance(data, list) else data.get("notes", data.get("note_list", []))
    normalized = []
    for note in notes:
        interact = note.get("interact_info", {})
        normalized.append({
            "title": note.get("title", note.get("display_title", ""))[:40],
            "liked": str(note.get("liked_count", interact.get("liked_count", ""))),
            "comment_count": str(note.get("comment_count", interact.get("comment_count", ""))),
            "status": note.get("status"),
            "note_id": note.get("note_id", note.get("id", "")),
            "time": (
                note.get("time")
                or note.get("timestamp")
                or note.get("create_time")
                or note.get("ctime")
            ),
        })
    return normalized


def normalize_notifications(data: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for message in data.get("message_list", []):
        user = message.get("user_info", {}) or {}
        item = message.get("item_info", {}) or {}
        normalized.append({
            "nickname": user.get("nickname", ""),
            "title": message.get("title", ""),
            "note_content": item.get("content", ""),
            "time": message.get("time", 0),
        })
    return normalized
