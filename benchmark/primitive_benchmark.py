import asyncio
import random
import secrets

import pytest

from benchmark.utils import execute

try:
    from pyignite.aio_cache import AioCache
except ImportError:
    AioCache = type('AioCache', (object,), {})

coro_batches = [5, 10, 20]


@pytest.mark.benchmark(group='long_put')
def benchmark_sync_long_put(benchmark, cache):
    def put():
        key = random.randint(0, 1024)
        cache.put(key, key)

    benchmark.pedantic(put, rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='long_put')
def benchmark_async_long_put(benchmark, event_loop, aio_cache):
    async def put():
        key = random.randint(0, 1024)
        await aio_cache.put(key, key)

    benchmark.pedantic(execute, args=(event_loop, put), rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='long_put')
@pytest.mark.parametrize('batch', coro_batches)
def benchmark_async_long_put_batch(benchmark, event_loop, aio_cache, batch):
    async def put():
        key = random.randint(0, 1024)
        await aio_cache.put(key, key)

    async def put_batched():
        await asyncio.gather(*[put() for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, put_batched), rounds=10, iterations=1000 // batch, warmup_rounds=10)


def load_long(cache, key_range):
    def inner_sync():
        for k in range(key_range):
            cache.put(k, k)

    async def inner_async():
        await asyncio.gather(*[cache.put(k, k) for k in range(key_range)])

    return inner_async() if isinstance(cache, AioCache) else inner_sync()


@pytest.mark.benchmark(group='long_get')
def benchmark_sync_long_get(benchmark, cache):
    load_long(cache, 1025)

    def get():
        key = random.randrange(0, 1025)
        val = cache.get(key)
        assert val == key

    benchmark.pedantic(get, rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='long_get')
def benchmark_async_long_get(benchmark, event_loop, aio_cache):
    event_loop.run_until_complete(load_long(aio_cache, 1025))

    async def get():
        key = random.randrange(0, 1025)
        val = await aio_cache.get(key)
        assert val == key

    benchmark.pedantic(execute, args=(event_loop, get), rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='long_get')
@pytest.mark.parametrize('batch', coro_batches)
def benchmark_async_long_get_batched(benchmark, event_loop, aio_cache, batch):
    event_loop.run_until_complete(load_long(aio_cache, 1025))

    async def get():
        key = random.randrange(0, 1025)
        val = await aio_cache.get(key)
        assert val == key

    async def get_batched():
        await asyncio.gather(*[get() for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, get_batched), rounds=10, iterations=1000 // batch, warmup_rounds=10)


def string_supplier(size):
    data = secrets.token_hex(size // 2)

    def supply(key=None):
        key = random.randrange(0, 1024) if key is None else key
        return key, data

    return supply


string_sizes = [128, 256, 1024, 2048, 4096]


@pytest.mark.benchmark(group='string_put')
@pytest.mark.parametrize('size', string_sizes)
def benchmark_sync_string_put(benchmark, cache, size):
    kv_supplier = string_supplier(size)

    def put():
        cache.put(*kv_supplier())

    benchmark.pedantic(put, rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='string_put')
@pytest.mark.parametrize('size', string_sizes)
def benchmark_async_string_put(benchmark, event_loop, aio_cache, size):
    kv_supplier = string_supplier(size)

    async def put():
        await aio_cache.put(*kv_supplier())

    benchmark.pedantic(execute, args=(event_loop, put), rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='string_put')
@pytest.mark.parametrize('batch', coro_batches)
@pytest.mark.parametrize('size', string_sizes)
def benchmark_async_string_put_batched(benchmark, event_loop, aio_cache, size, batch):
    kv_supplier = string_supplier(size)

    async def put():
        await aio_cache.put(*kv_supplier())

    async def put_batched():
        await asyncio.gather(*[put() for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, put_batched), rounds=10, iterations=1000 // batch, warmup_rounds=10)


def load_data(cache, kv_supplier, key_range):
    def inner_sync():
        for k in range(key_range):
            cache.put(*kv_supplier(k))

    async def inner_async():
        await asyncio.gather(*[cache.put(*kv_supplier(k)) for k in range(key_range)])

    return inner_async() if isinstance(cache, AioCache) else inner_sync()


@pytest.mark.benchmark(group='string_get')
@pytest.mark.parametrize('size', string_sizes)
def benchmark_sync_string_get(benchmark, cache, size):
    kv_supplier = string_supplier(size)
    load_data(cache, kv_supplier, 1025)

    def get():
        k = random.randrange(0, 1025)
        assert cache.get(k) == kv_supplier()[1]

    benchmark.pedantic(get, rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='string_get')
@pytest.mark.parametrize('size', string_sizes)
def benchmark_async_string_get(benchmark, event_loop, aio_cache, size):
    kv_supplier = string_supplier(size)
    event_loop.run_until_complete(load_data(aio_cache, kv_supplier, 1025))

    async def get():
        k = random.randrange(0, 1025)
        assert await aio_cache.get(k) == kv_supplier()[1]

    benchmark.pedantic(execute, args=(event_loop, get), rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='string_get')
@pytest.mark.parametrize('batch', coro_batches)
@pytest.mark.parametrize('size', string_sizes)
def benchmark_async_string_get_batched(benchmark, event_loop, aio_cache, size, batch):
    kv_supplier = string_supplier(size)
    event_loop.run_until_complete(load_data(aio_cache, kv_supplier, 1025))

    async def get():
        k = random.randrange(0, 1025)
        assert await aio_cache.get(k) == kv_supplier()[1]

    async def get_batched():
        await asyncio.gather(*[get() for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, get_batched), rounds=10, iterations=1000 // batch, warmup_rounds=10)
