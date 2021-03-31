import pytest
import uvloop
from pyignite import AioClient, Client


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


@pytest.fixture(params=['partition_aware', 'simple'])
async def aio_client(request, ignite_hosts):
    client = AioClient(partition_aware=request.param == 'partition_aware')
    try:
        await client.connect(ignite_hosts)
        yield client
    finally:
        await client.close()


@pytest.fixture(params=['partition_aware', 'simple'])
def client(request, ignite_hosts):
    client = Client(partition_aware=request.param == 'partition_aware')
    try:
        client.connect(ignite_hosts)
        yield client
    finally:
        client.close()


def pytest_addoption(parser):
    parser.addini("ignite_connection", default="127.0.0.1:10800", help="ignite connection string")
