def execute(loop, coro, *args, **kwargs):
    loop.run_until_complete(coro(*args, **kwargs))