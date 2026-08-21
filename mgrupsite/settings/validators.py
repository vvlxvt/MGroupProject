def is_weak_secret_key(value: str) -> bool:
    normalized = value.strip()
    return (
        len(normalized) < 50
        or len(set(normalized)) < 5
        or normalized.startswith("django-insecure-")
        or normalized.lower() in {"change-me", "changeme", "secret"}
    )
