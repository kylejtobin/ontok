"""One server per session, declared as the deployment declares it: an account, an administrative
identity, a program identity with exactly its permissions, and the EVENTS stream."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import nats
import pytest
import pytest_asyncio
from nats.aio.client import Client
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

IMAGE = "nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3"


@pytest.fixture(scope="session")
def server() -> Iterator[str]:
    container = (
        DockerContainer(IMAGE)
        .with_volume_mapping(str(Path(__file__).parent), "/etc/nats", "ro")
        .with_command("-c /etc/nats/nats.conf")
        .with_exposed_ports(4222)
    )
    with container:
        wait_for_logs(container, "Server is ready")
        yield f"nats://{container.get_container_host_ip()}:{container.get_exposed_port(4222)}"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def stream(server: str) -> AsyncIterator[None]:
    admin = await nats.connect(server, user="admin", password="admin")  # pyright: ignore[reportUnknownMemberType]
    await admin.jetstream().add_stream(  # pyright: ignore[reportUnknownMemberType]
        StreamConfig(
            name="EVENTS",
            subjects=["event.>"],
            retention=RetentionPolicy.LIMITS,
            storage=StorageType.FILE,
            deny_delete=True,
            deny_purge=True,
            allow_direct=True,
            allow_atomic=True,
        )
    )
    yield
    await admin.close()


@pytest_asyncio.fixture(loop_scope="session")
async def program(server: str, stream: None) -> AsyncIterator[Client]:
    client = await nats.connect(server, user="program", password="program")  # pyright: ignore[reportUnknownMemberType]
    yield client
    await client.close()


@pytest_asyncio.fixture(loop_scope="session")
async def admin(server: str, stream: None) -> AsyncIterator[Client]:
    client = await nats.connect(server, user="admin", password="admin")  # pyright: ignore[reportUnknownMemberType]
    yield client
    await client.close()
