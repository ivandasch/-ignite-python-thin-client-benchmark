import asyncio
import random

import pytest

from benchmark.utils import execute

coro_batches = [5, 10, 20]

CREATE_QUERY = '''
    CREATE TABLE DATA (
    id INT(11) PRIMARY KEY,
    name CHAR(24)
    )
'''

DROP_QUERY = '''
    DROP TABLE DATA IF EXISTS
'''

INSERT_QUERY = '''
    MERGE INTO DATA (id, name) VALUES (?, ?)
'''


@pytest.fixture
def sql_cache(client):
    client.sql(CREATE_QUERY)
    yield None
    client.sql(DROP_QUERY)


@pytest.mark.benchmark(group='sql_insert')
def benchmark_sync_insert(benchmark, client, sql_cache):
    def insert():
        key = random.randint(0, 1024)
        client.sql(INSERT_QUERY, query_args=[key, f'name_{key}'])

    benchmark.pedantic(insert, rounds=10, iterations=1000, warmup_rounds=10)


@pytest.fixture
async def async_sql_cache(aio_client):
    await aio_client.sql(CREATE_QUERY)
    yield None
    await aio_client.sql(DROP_QUERY)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='sql_insert')
def benchmark_async_insert(benchmark, event_loop, aio_client, async_sql_cache):
    async def insert():
        key = random.randint(0, 1024)
        await aio_client.sql(INSERT_QUERY, query_args=[key, f'name_{key}'])

    benchmark.pedantic(execute, args=(event_loop, insert), rounds=10, iterations=1000, warmup_rounds=10)


@pytest.mark.async_bench
@pytest.mark.benchmark(group='sql_insert')
@pytest.mark.parametrize('batch', coro_batches)
def benchmark_async_insert_batched(benchmark, event_loop, aio_client, async_sql_cache, batch):
    async def insert():
        key = random.randint(0, 1024)
        await asyncio.gather(*[
            aio_client.sql(INSERT_QUERY, query_args=[k, f'name_{k}']) for k in range(key, key + batch)
        ])

    benchmark.pedantic(execute, args=(event_loop, insert), rounds=10, iterations=1000 // batch, warmup_rounds=10)
