# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from logging import getLogger
from os import getenv
from pathlib import Path

from celery import Celery
from fedora_messaging import config
from fedora_messaging.message import Message

from packit_service_fedmsg.callbacks import get_callback

config.conf.setup_logging()
logger = getLogger(__name__)


class Consumerino:
    """
    Consumer of events from Fedora Messaging.
    """

    def __init__(self):
        self._celery_app = None
        self.environment = getenv("DEPLOYMENT")
        self.packit_user = {"prod": "packit", "stg": "packit-stg"}.get(
            self.environment,
            "packit",
        )

        self.configure_sentry()

    @property
    def celery_app(self):
        if self._celery_app is None:
            host = getenv("REDIS_SERVICE_HOST", "redis")
            password = getenv("REDIS_PASSWORD", "")
            port = getenv("REDIS_SERVICE_PORT", "6379")
            db = getenv("REDIS_SERVICE_DB", "0")
            broker_url = f"redis://:{password}@{host}:{port}/{db}"
            logger.debug(f"Celery uses redis @ {host}:{port}/{db}")

            self._celery_app = Celery(broker=broker_url)
            # https://docs.celeryq.dev/en/latest/userguide/configuration.html#std-setting-task_default_queue
            self._celery_app.conf.task_default_queue = "short-running"
        return self._celery_app

    @staticmethod
    def configure_sentry():
        secret_key = getenv("SENTRY_SECRET")
        if not secret_key:
            return

        import sentry_sdk

        # with the use of default integrations
        # https://docs.sentry.io/platforms/python/configuration/integrations/default-integrations/
        sentry_sdk.init(secret_key, environment=getenv("DEPLOYMENT"))

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("runner-type", "packit-service-fedmsg")

    def __call__(self, message: Message):
        """
        Invoked when a message is received by the consumer.
        Create Celery task from Fedora Messaging.

        Args:
            message: Message from the Fedora Messaging bus.
        """
        Path(getenv("LIVENESS_FILE", "/tmp/liveness")).touch(exist_ok=True)

        event = message.body
        topic = message.topic
        result = get_callback(topic)(topic, event, self.packit_user)

        if result.msg:
            logger.info(result.msg)

        if not result.pass_to_service:
            return

        event["topic"] = topic
        event["timestamp"] = datetime.now(timezone.utc).timestamp()

        task = self.celery_app.send_task(
            name="task.steve_jobs.process_message",
            kwargs={
                "event": event,
                "source": "fedora-messaging",
                "event_type": topic.removeprefix("org.fedoraproject.prod."),
            },
        )
        logger.debug(f"Task UUID={task.id} sent to Celery")
