import pytest
import uvloop

from pyignite import Client
from pyignite.exceptions import ParameterError

try:
    from pyignite import AioClient
    WITH_ASYNC = True
except ImportError:
    AioClient = None
    WITH_ASYNC = False


try:
    Client(partition_aware=True)
    WITH_PARTITION_AWARE = True
except ParameterError:
    WITH_PARTITION_AWARE = False


@pytest.fixture(autouse=True)
def skip_if_not_async(request):
    if request.node.get_closest_marker('async_bench') and not WITH_ASYNC:
        pytest.skip('skipped async_bench: asyncio is not supported')


def pytest_configure(config):
    marker_docs = [
        "async_bench: mark benchmark as async bench and skip if pyignite doesn't support asyncio",
    ]

    for marker_doc in marker_docs:
        config.addinivalue_line("markers", marker_doc)


@pytest.fixture
def event_loop():
    loop = uvloop.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def ignite_hosts(request):
    conn_str = request.config.getini("ignite_connection")

    hosts = []
    for pair in conn_str.split(","):
        host, port = pair.split(":")
        hosts.append((host, int(port)))

    return hosts


part_aware_params = ['simple']
if WITH_PARTITION_AWARE:
    part_aware_params.append('partition_aware')

@pytest.fixture(params=part_aware_params)
async def aio_client(request, ignite_hosts):
    if request.param == 'partition_aware':
        client = AioClient(partition_aware=True)
    else:
        client = AioClient()
    try:
        await client.connect(ignite_hosts)
        yield client
    finally:
        await client.close()


@pytest.fixture(params=part_aware_params)
def client(request, ignite_hosts):
    if request.param == 'partition_aware':
        client = Client(partition_aware=True)
    else:
        client = Client()
    try:
        client.connect(ignite_hosts)
        yield client
    finally:
        client.close()


@pytest.fixture()
def cache(request, client):
    cache = client.get_or_create_cache(request.node.name)
    yield cache
    cache.destroy()


@pytest.fixture()
async def aio_cache(request, aio_client):
    cache = await aio_client.get_or_create_cache(request.node.name)
    yield cache
    await cache.destroy()


def pytest_addoption(parser):
    parser.addini("ignite_connection", default="127.0.0.1:10800", help="ignite connection string")
