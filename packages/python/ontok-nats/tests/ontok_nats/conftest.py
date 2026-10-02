"""The server the conformance tests run against: one nats-server container for the session,
with the organization's stream and bucket created as an operator would."""

from collections.abc import AsyncIterator, Iterator
from datetime import timedelta
from pathlib import Path

import nats
import pytest
import pytest_asyncio
from nats.aio.client import Client
from nats.js.api import StreamConfig
from nats.js.client import JetStreamContext
from pydantic import NatsDsn, SecretStr
from testcontainers.compose import DockerCompose

from ontok.core import PositiveDuration
from ontok.nats import Bucket, MaxDeliver, NatsConfig, ServerUrl, StreamName, User


@pytest.fixture(scope="session")
def server() -> Iterator[DockerCompose]:
    compose = DockerCompose(Path(__file__).parent, compose_file_name="compose.yaml", wait=True)
    compose.start()
    yield compose
    compose.stop()


@pytest.fixture(scope="session")
def config(server: DockerCompose) -> NatsConfig:
    host = server.get_service_host("nats", 4222)
    port = server.get_service_port("nats", 4222)
    return NatsConfig(
        url=ServerUrl(NatsDsn(f"nats://{host}:{port}")),
        user=User("program"),
        credentials=SecretStr("none"),
        stream=StreamName("EVENTS"),
        bucket=Bucket("RM"),
        ack_wait=PositiveDuration(timedelta(seconds=1)),
        max_deliver=MaxDeliver(3),
        reply_wait=PositiveDuration(timedelta(seconds=5)),
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def connection(config: NatsConfig) -> AsyncIterator[Client]:
    client = await nats.connect(  # pyright: ignore[reportUnknownMemberType]
        f"{config.url.root}",
        user=config.user.root,
        password=config.credentials.get_secret_value(),
        reconnect_time_wait=0.2,
        max_reconnect_attempts=-1,
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def jetstream(connection: Client, config: NatsConfig) -> JetStreamContext:
    context = connection.jetstream()  # pyright: ignore[reportUnknownMemberType]
    await context.add_stream(  # pyright: ignore[reportUnknownMemberType]
        StreamConfig(name=config.stream.root, subjects=["event.>"], allow_atomic=True)
    )
    await context.create_key_value(bucket=config.bucket.root)  # pyright: ignore[reportUnknownMemberType]
    return context
