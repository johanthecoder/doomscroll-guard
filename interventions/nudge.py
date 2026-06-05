from plyer import notification


def send_nudge() -> None:
    try:
        notification.notify(
            title="Doomscroll Guard",
            message="Hey — get back to work.",
            timeout=5,
        )
    except Exception:
        pass
