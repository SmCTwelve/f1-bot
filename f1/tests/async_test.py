"""Asynchronous test wrapper."""
import asyncio


def async_test(coro):
    """Runs the test case as a coroutine in a new event loop. Use as decorator to the test function.

    Example:

    ```
    @async_test
    async def test_method(self):
        await self.async_task()
    ```
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper
