import time

def long_task(seconds: int = 5):
    time.sleep(seconds)
    return {"ok": True, "message": f"done in {seconds}s"}
