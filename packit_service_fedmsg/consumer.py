# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from functools import reduce
from logging import getLogger
from os import getenv
from pathlib import Path
from typing import Any

from celery import Celery
from fedora_messaging import config
from fedora_messaging.message import Message

config.conf.setup_logging()
logger = getLogger(__name__)

# !!! When new topics are added/removed here, then they must be added/removed also in a
# respective fedora.toml.j2 (https://github.com/packit/deployment/tree/main/secrets) !!!

COPR_TOPICS = {
    "org.fedoraproject.prod.copr.build.end",
    "org.fedoraproject.prod.copr.build.start",
}
KOJI_TOPICS = {
    "org.fedoraproject.prod.buildsys.task.state.change",
    "org.fedoraproject.prod.buildsys.build.state.change",
}

DISTGIT_PUSH_TOPIC = "org.fedoraproject.prod.git.receive"
DISTGIT_PR_CLOSED_TOPIC = "org.fedoraproject.prod.pagure.pull-request.closed"

DISTGIT_PR_FLAG_TOPIC = {
    "org.fedoraproject.prod.pagure.pull-request.flag.added",
    "org.fedoraproject.prod.pagure.pull-request.flag.updated",
}

NEW_HOTNESS_TOPIC = "org.fedoraproject.prod.hotness.update.bug.file"

DISTGIT_PR_COMMENT_ADDED = "org.fedoraproject.prod.pagure.pull-request.comment.added"


def nested_get(d: dict, *keys, default=None) -> Any:
    """
    recursively obtain value from nested dict

    :param d: dictionary
    :param keys: path within the structure
    :param default: a value to return by default

    :return: value or None
    """
    response = d
    for k in keys:
        try:
            response = response[k]
        except (KeyError, AttributeError, TypeError):
            # logger.debug("can't obtain %s: %s", k, ex)
            return default
    return response


def specfile_changed(body: dict) -> bool:
    """
    Does the commit contain specfile change?
    :param body: message body
    :return: bool
    """
    files = reduce(
        lambda val, key: val.get(key) if val else None,
        ["commit", "stats", "files"],
        body,
    )
    file_names = files.keys() if files else []

    return any(file_name.endswith(".spec") for file_name in file_names)


class Consumerino:
    """
    Consume events from fedora messaging
    """

    def __init__(self):
        self._celery_app = None
        self.environment = getenv("DEPLOYMENT")
        self.packit_user = {"prod": "packit", "stg": "packit-stg"}.get(
            self.environment, "packit"
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
        Create celery task from fedora message
        :param message: Message from Fedora message bus
        :return: None
        """
        event = message.body
        topic = message.topic
        what = ""

        Path(getenv("LIVENESS_FILE", "/tmp/liveness")).touch(exist_ok=True)

        if topic in COPR_TOPICS:
            if event.get("user") != self.packit_user:
                logger.info(f"Copr build not built by {self.packit_user}!")
                return
            what = event.get("what")

        # TODO: accept builds run by other owners as well
        #  (For the `bodhi_update` job.)
        elif topic in KOJI_TOPICS:
            if event.get("owner") != self.packit_user:
                logger.info(f"Koji build not built by {self.packit_user}!")
                return
            if "buildsys.build.state" in topic:
                what = (
                    f"build:{event.get('build_id')} task:{event.get('task_id')}"
                    f" {event.get('old')}->{event.get('new')}"
                )
            if "buildsys.task.state" in topic:  # scratch build
                what = f"id:{event.get('id')} {event.get('old')}->{event.get('new')}"

        elif topic == DISTGIT_PUSH_TOPIC:
            if getenv("PROJECT", "").startswith("packit") and not specfile_changed(
                event
            ):
                logger.info("No specfile change, dropping the message.")
                return
            if commit := event.get("commit"):
                what = (
                    f"{commit.get('repo')} {commit.get('branch')} {commit.get('rev')}"
                )

        elif topic in DISTGIT_PR_FLAG_TOPIC:
            if nested_get(event, "pullrequest", "user", "name") != self.packit_user:
                logger.info(
                    f"Flag added/changed in a PR not created by {self.packit_user}"
                )
                return
            what = (
                f"{nested_get(event, 'pullrequest', 'project', 'fullname')}"
                f" '{nested_get(event, 'flag', 'comment')}'"
            )

        elif topic == DISTGIT_PR_CLOSED_TOPIC:
            if not nested_get(event, "pullrequest", "merged"):
                logger.info("Pull request was not merged.")
                return

        elif topic == DISTGIT_PR_COMMENT_ADDED:
            comments = nested_get(event, "pullrequest", "comments")
            last_comment = comments[-1]
            what = (
                f" For {nested_get(event, 'pullrequest', 'project', 'fullname')}"
                f" new comment: '{last_comment['comment']}'"
                f" from {last_comment['user']['name']}"
            )

        elif topic == NEW_HOTNESS_TOPIC:
            package = event.get("package")
            version = nested_get(event, "trigger", "msg", "project", "version")

            what = f" New hotness update: version {version} of package {package}."

        if what:
            logger.info(what)

        event["topic"] = topic
        event["timestamp"] = datetime.now(timezone.utc).timestamp()

        result = self.celery_app.send_task(
            name="task.steve_jobs.process_message",
            kwargs={
                "event": event,
                "source": "fedora-messaging",
                "event_type": topic.removeprefix("org.fedoraproject.prod."),
            },
        )
        logger.debug(f"Task UUID={result.id} sent to Celery")
