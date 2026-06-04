import asyncio
import traceback
from typing import Awaitable, Callable


pro_queue = asyncio.Queue()
free_queue = asyncio.Queue()


async def add_to_queue(
    user_id: int,
    task_name: str,
    task_func: Callable[[], Awaitable[None]],
    is_pro: bool = False
):
    job = {
        "user_id": user_id,
        "task_name": task_name,
        "task_func": task_func
    }

    if is_pro:
        await pro_queue.put(job)
        return pro_queue.qsize()

    await free_queue.put(job)
    return free_queue.qsize()


async def queue_worker(worker_id: int = 1):
    while True:
        if not pro_queue.empty():
            job = await pro_queue.get()
            queue = pro_queue
        elif not free_queue.empty():
            job = await free_queue.get()
            queue = free_queue
        else:
            await asyncio.sleep(0.05)
            continue

        try:
            print(f"WORKER {worker_id}: {job['task_name']}")
            await job["task_func"]()
        except Exception as e:
            print(f"QUEUE ERROR in {job['task_name']}: {e}")
            traceback.print_exc()
        finally:
            queue.task_done()