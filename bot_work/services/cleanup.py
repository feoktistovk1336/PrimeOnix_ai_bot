import os
import time


def cleanup_generated_posts(days: int = 7):
    folder = "generated_posts"

    if not os.path.exists(folder):
        return 0

    now = time.time()
    max_age = days * 24 * 60 * 60
    deleted = 0

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            continue

        if now - os.path.getmtime(path) > max_age:
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                pass

    return deleted