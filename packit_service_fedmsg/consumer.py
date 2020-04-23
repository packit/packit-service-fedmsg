# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from datetime import datetime
from logging import getLogger
from os import getenv

from celery import Celery
from fedora_messaging import api, config
from fedora_messaging.message import Message

config.conf.setup_logging()
logger = getLogger(__name__)

INTERESTED_TOPICS = {
    "org.fedoraproject.prod.copr.build.end",
    "org.fedoraproject.prod.copr.build.start",
}


class Consumerino:
    """
    Consume events from fedora messaging
    """

    def __init__(self):
        self._celery_app = None

    @property
    def celery_app(self):
        if self._celery_app is None:
            redis_host = getenv("REDIS_SERVICE_HOST", "localhost")
            redis_port = getenv("REDIS_SERVICE_PORT", "6379")
            redis_db = getenv("REDIS_SERVICE_DB", "0")
            redis_url = "redis://{host}:{port}/{db}".format(
                host=redis_host, port=redis_port, db=redis_db
            )

            self._celery_app = Celery(backend=redis_url, broker=redis_url)
        return self._celery_app

    @staticmethod
    def configure_sentry():
        secret_key = getenv("SENTRY_SECRET")
        if not secret_key:
            return

        import sentry_sdk

        # with the use of default integrations
        # https://docs.sentry.io/platforms/python/default-integrations/
        sentry_sdk.init(secret_key, environment=getenv("DEPLOYMENT"))

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("runner-type", "packit-service-fedmsg")

    def fedora_messaging_callback(self, message: Message):
        """
        Create celery task from fedora message
        :param message: Message from Fedora message bus
        :return: None
        """
        if message.body.get("user") != "packit":
            logger.info("Not built by packit!")
            return

        if message.topic not in INTERESTED_TOPICS:
            logger.debug("Not interested topic")
            return

        logger.info(message.body.get("what"))
        message.body["topic"] = message.topic
        message.body["timestamp"] = datetime.utcnow().timestamp()
        self.celery_app.send_task(
            name="task.steve_jobs.process_message", kwargs={"event": message.body}
        )

    def consume_from_fedora_messaging(self):
        """
        fedora-messaging is written in an async way: callbacks
        """
        # Start consuming messages using our callback. This call will block until
        # a KeyboardInterrupt is raised, or the process receives a SIGINT or SIGTERM
        # signal.

        self.configure_sentry()
        api.consume(self.fedora_messaging_callback)
