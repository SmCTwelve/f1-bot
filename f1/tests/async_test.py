'''Asynchronous test wrapper. Runs the test case in a new event loop and returns the awaitable Future.

Example:

```@async_test
async test_method(self):
    await self.async_task()
```
'''
import asyncio


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper
