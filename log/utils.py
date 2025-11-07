from .models import LogEntry

def log_action(user, *, action, entity_type, entity_id=None, entity_label="", details=""):
    username_cache = ""
    if user:
        try:
            username_cache = getattr(user, "get_full_name", lambda: "")() or user.get_username()
        except Exception:
            username_cache = ""

    return LogEntry.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        username_cache=username_cache[:150],
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_label=entity_label or "",
        details=details or "",
    )
