import asyncio
import logging
from os import environ
from time import sleep
from typing import AsyncGenerator

import asyncpg
import docker
import pytest
from _pytest.monkeypatch import MonkeyPatch
from confluent_kafka.admin import AdminClient, NewTopic  # noqa
from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from faker import Faker
from piccolo.apps.migrations.commands.forwards import forwards
from piccolo.utils.sync import run_sync

fake = Faker()

logger = logging.getLogger()

#  from pytest.ini
KAFKA_IMAGE_NAME = environ.get("KAFKA_IMAGE_NAME")
ZOOKEEPER_IMAGE_NAME = environ.get("ZOOKEEPER_IMAGE_NAME")
ZOOKEEPER_CLIENT_PORT = environ.get("ZOOKEEPER_CLIENT_PORT")
BROKER_PORT = environ.get("BROKER_PORT")
LOCAL_PORT = environ.get("LOCAL_PORT")

POSTGRES_IMAGE_NAME = environ.get("POSTGRES_IMAGE_NAME")
METAMORPH_DATABASE_USER = environ.get("METAMORPH_DATABASE_USER")
METAMORPH_DATABASE_HOST = environ.get("METAMORPH_DATABASE_HOST")
METAMORPH_DATABASE_PORT = environ.get("METAMORPH_DATABASE_PORT")
BOOTSTRAP_SERVERS = environ.get("BOOTSTRAP_SERVERS")


def pytest_addoption(parser):
    parser.addoption("--fixture_scope")


def determine_scope(fixture_name, config):
    fixture_scope = config.getoption("--fixture_scope")
    if fixture_scope in [
        "function",
        "class",
        "module",
        "package",
        "session",
    ]:
        return fixture_scope
    else:
        raise ValueError(
            "Usage: pytest tests/ --fixture_scope=function|class|module|package|session"
        )


# General fixture(s)
@pytest.fixture(scope=determine_scope)
def resource_postfix() -> str:
    return fake.color_name().lower()


# Docker fixture(s)
@pytest.fixture(scope=determine_scope)
def docker_client() -> DockerClient:
    return docker.from_env()


@pytest.fixture(scope=determine_scope)
def network(docker_client: DockerClient, resource_postfix: str) -> Network:
    _network = docker_client.networks.create(name=f"network-{resource_postfix}")
    yield _network
    _network.remove()


# Zookeeper fixture(s)
@pytest.fixture(scope=determine_scope)
def zookeeper(
    docker_client: DockerClient, network: Network, resource_postfix: str
) -> Container:
    logger.info(f"Pulling {ZOOKEEPER_IMAGE_NAME}")
    docker_client.images.get(name=ZOOKEEPER_IMAGE_NAME)
    logger.info(f"Starting container zookeeper-{resource_postfix}")

    zookeeper_container = docker_client.containers.run(
        image=ZOOKEEPER_IMAGE_NAME,
        ports={f"{ZOOKEEPER_CLIENT_PORT}/tcp": f"{ZOOKEEPER_CLIENT_PORT}/tcp"},
        network=network.name,
        name=f"zookeeper-{resource_postfix}",
        hostname="zookeeper",
        environment={"ZOOKEEPER_CLIENT_PORT": ZOOKEEPER_CLIENT_PORT},
        detach=True,
    )
    logger.info(f"Container zookeeper-{resource_postfix} started")
    yield zookeeper_container
    zookeeper_container.remove(force=True)


# Kafka fixture(s)
@pytest.fixture(scope=determine_scope)
def topic_name(resource_postfix: str) -> str:
    return f"demo-topic-{resource_postfix}"


@pytest.fixture(scope=determine_scope)
def consumer_id(resource_postfix: str) -> str:
    return f"demo-consumer-{resource_postfix}"


@pytest.fixture(scope=determine_scope)
def broker(
    docker_client: DockerClient,
    network: Network,
    zookeeper: Container,
    resource_postfix: str,
) -> Container:
    logger.info(f"Pulling {KAFKA_IMAGE_NAME}")
    docker_client.images.get(name=KAFKA_IMAGE_NAME)
    logger.info(f"Starting container broker-{resource_postfix}")
    broker_container = docker_client.containers.run(
        image=KAFKA_IMAGE_NAME,
        ports={
            f"{BROKER_PORT}/tcp": f"{BROKER_PORT}/tcp",
            f"{LOCAL_PORT}/tcp": f"{LOCAL_PORT}/tcp",
        },
        network=network.name,
        name=f"broker-{resource_postfix}",
        hostname="broker",
        environment={
            "KAFKA_BROKER_ID": 25,
            "KAFKA_ZOOKEEPER_CONNECT": f"{zookeeper.name}:{ZOOKEEPER_CLIENT_PORT}",
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
            "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://broker:{BROKER_PORT},PLAINTEXT_HOST://localhost:{LOCAL_PORT}",
            "KAFKA_METRIC_REPORTERS": "io.confluent.metrics.reporter.ConfluentMetricsReporter",
            "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
            "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
            "KAFKA_CONFLUENT_LICENSE_TOPIC_REPLICATION_FACTOR": 1,
            "KAFKA_CONFLUENT_BALANCER_TOPIC_REPLICATION_FACTOR": 1,
            "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": 1,
            "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": 1,
            "KAFKA_JMX_PORT": 9101,
            "KAFKA_JMX_HOSTNAME": "localhost",
            "CONFLUENT_METRICS_REPORTER_BOOTSTRAP_SERVERS": f"broker:{BROKER_PORT}",
            "CONFLUENT_METRICS_REPORTER_TOPIC_REPLICAS": 1,
            "CONFLUENT_METRICS_ENABLE": "true",
            "CONFLUENT_SUPPORT_CUSTOMER_ID": "anonymous",
        },
        detach=True,
    )
    logger.info(f"Container broker-{resource_postfix} started")
    yield broker_container
    broker_container.remove(force=True)


@pytest.fixture(scope=determine_scope)
def kafka_admin_client(broker: Container) -> AdminClient:
    has_started = False
    kafka_logs = set()
    while not has_started:
        log_line = broker.logs(tail=1).decode("UTF-8").strip()
        if log_line in kafka_logs:
            pass
        else:
            kafka_logs.add(log_line)
            logger.info(log_line)
        if "INFO Kafka startTimeMs" in log_line:
            has_started = True
            logger.info("Kafka has started")

    admin_client = AdminClient(conf={"bootstrap.servers": f"0.0.0.0:{LOCAL_PORT}"})

    return admin_client


@pytest.fixture(scope=determine_scope)
def new_topic(kafka_admin_client: AdminClient, topic_name: str) -> NewTopic:
    new_topic = NewTopic(
        topic=topic_name,
        num_partitions=1,
        replication_factor=1,
    )
    kafka_admin_client.create_topics(new_topics=[new_topic])
    topic_exists = False
    while not topic_exists:
        logger.info(f"Waiting for topic {new_topic.topic} to be created")
        sleep(1)
        cluster_metadata = kafka_admin_client.list_topics()
        topics = cluster_metadata.topics
        topic_exists = new_topic.topic in topics.keys()
    yield new_topic
    kafka_admin_client.delete_topics(topics=[new_topic.topic])


# Database fixture(s)
@pytest.fixture(scope=determine_scope)
def metamorph_database_name(resource_postfix: str):
    _value = f"metamorph_{resource_postfix}"
    MonkeyPatch().setenv(name="METAMORPH_DATABASE_NAME", value=_value)
    return _value


@pytest.fixture(scope=determine_scope)
def metamorph_database_password() -> str:
    _value = fake.password()
    MonkeyPatch().setenv(name="METAMORPH_DATABASE_PASSWORD", value=_value)
    return _value


@pytest.fixture(scope=determine_scope)
def postgres(
    docker_client: DockerClient,
    network: Network,
    resource_postfix: str,
    metamorph_database_password: str,
) -> Container:
    logger.info(f"Pulling {POSTGRES_IMAGE_NAME}")
    docker_client.images.get(name=POSTGRES_IMAGE_NAME)
    logger.info(f"Starting container postgres-{resource_postfix}")

    postgres_container = docker_client.containers.run(
        image=POSTGRES_IMAGE_NAME,
        ports={f"{METAMORPH_DATABASE_PORT}/tcp": f"{METAMORPH_DATABASE_PORT}/tcp"},
        network=network.name,
        name=f"postgres-{resource_postfix}",
        hostname="postgres",
        environment={
            "POSTGRES_PASSWORD": metamorph_database_password,
            "POSTGRES_HOST_AUTH_METHOD": "trust",
        },
        detach=True,
    )

    yield postgres_container
    postgres_container.remove(force=True)


@pytest.fixture(scope=determine_scope)
def event_loop(request):
    """
    Create an instance of the default event loop for each test case.
    This overrides the event_loop function in: site-packages/pytest_asyncio/plugin.py
    Without this override the code would fail with ScopeMismatch
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope=determine_scope)
async def create_database(
    postgres: Container, metamorph_database_name: str, metamorph_database_password: str
) -> AsyncGenerator:
    is_ready_exit_code = 1
    while is_ready_exit_code != 0:
        is_ready_exit_code = postgres.exec_run(cmd="pg_isready").exit_code
        sleep(1)

    connection = await asyncpg.connect(
        host=METAMORPH_DATABASE_HOST,
        port=METAMORPH_DATABASE_PORT,
        user=METAMORPH_DATABASE_USER,
        password=metamorph_database_password,
    )

    query = f"create database {metamorph_database_name}"  # noqa
    await connection.execute(query=query)
    run_sync(forwards(app_name="metamorph", migration_id="all"))

    yield metamorph_database_name

    query = f"drop database {metamorph_database_name}"  # noqa
    await connection.execute(query=query)
    await connection.close()
