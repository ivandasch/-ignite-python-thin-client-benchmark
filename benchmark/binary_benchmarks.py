import asyncio
import random
import secrets
from collections import OrderedDict

import pytest
from pyignite import GenericObjectMeta

try:
    from pyignite.aio_cache import AioCache
except ImportError:
    AioCache = None

from pyignite.datatypes import IntObject, ByteArrayObject

data_sizes = [1024, 4096, 10 * 1024, 100 * 1024, 500 * 1024, 1024 * 1024]
coro_batches = [5, 10, 20]


class Data(
    metaclass=GenericObjectMeta,
    type_name='Data',
    schema=OrderedDict([
        ('id', IntObject),
        ('data', ByteArrayObject)
    ])
):
    pass


def binary_object_supplier(size):
    data = secrets.token_bytes(size)

    def supply(key=None):
        key = random.randrange(0, 1024) if key is None else key
        return key, Data(id=key, data=data)

    return supply


def execute(loop, coro, *args, **kwargs):
    loop.run_until_complete(coro(*args, **kwargs))


@pytest.fixture()
async def aio_cache(request, aio_client):
    cache = await aio_client.get_or_create_cache(request.node.name)
    yield cache
    await cache.destroy()


@pytest.mark.async_bench
@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.benchmark
@pytest.mark.benchmark(group='binary_object_put')
def benchmark_async_binary_put(benchmark, event_loop, aio_cache, size):
    kv_supplier = binary_object_supplier(size)

    async def put():
        await aio_cache.put(*kv_supplier())

    benchmark.pedantic(execute, args=(event_loop, put), rounds=10, iterations=100, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.parametrize('batch', coro_batches)
@pytest.mark.benchmark(group='binary_object_put')
def benchmark_async_binary_put_batch(benchmark, event_loop, aio_cache, batch, size):
    kv_supplier = binary_object_supplier(size)

    async def put_batched(batch):
        await asyncio.gather(*[aio_cache.put(*kv_supplier()) for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, put_batched, batch),
                       rounds=10, iterations=100 // batch, warmup_rounds=10)


@pytest.fixture()
def cache(request, client):
    cache = client.get_or_create_cache(request.node.name)
    yield cache
    cache.destroy()


@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.benchmark(group='binary_object_put')
def benchmark_sync_binary_put(benchmark, cache, size):
    kv_supplier = binary_object_supplier(size)

    def put():
        cache.put(*kv_supplier())

    benchmark.pedantic(put, rounds=10, iterations=100, warmup_rounds=10)


def load_data(cache, size, key_range):
    kv_supplier = binary_object_supplier(size)

    def inner_sync():
        for k in range(key_range):
            cache.put(*kv_supplier(k))

    async def inner_async():
        await asyncio.gather(*[cache.put(*kv_supplier(k)) for k in range(key_range)])

    return inner_async() if isinstance(cache, AioCache) else inner_sync()


@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.benchmark(group='binary_object_get')
def benchmark_sync_binary_get(benchmark, cache, size):
    load_data(cache, size, 1024)

    def get():
        k = random.randrange(0, 1024)
        v = cache.get(k)
        assert v and v.id == k

    benchmark.pedantic(get, rounds=10, iterations=100, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.benchmark(group='binary_object_get')
def benchmark_async_binary_get(benchmark, event_loop, aio_cache, size):
    event_loop.run_until_complete(load_data(aio_cache, size, 1024))

    async def get():
        k = random.randrange(0, 1024)
        v = await cache.get(k)
        assert v and v.id == k

    benchmark.pedantic(execute, args=(event_loop, get), rounds=10, iterations=100, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.parametrize('size', data_sizes)
@pytest.mark.parametrize('batch', coro_batches)
@pytest.mark.benchmark(group='binary_object_get')
def benchmark_async_binary_get_batch(benchmark, event_loop, aio_cache, batch, size):
    event_loop.run_until_complete(load_data(aio_cache, size, 1024))

    async def get():
        k = random.randrange(0, 1024)
        v = await aio_cache.get(k)
        assert v and v.id == k

    async def get_batched(batch):
        await asyncio.gather(*[get() for _ in range(0, batch)])

    benchmark.pedantic(execute, args=(event_loop, get_batched, batch),
                       rounds=10, iterations=100 // batch, warmup_rounds=10)
