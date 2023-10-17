# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from os import getenv
from typing import Callable

from packit_service_fedmsg.utils import nested_get, specfile_changed


@dataclass
class CallbackResult:
    """
    Represents the result of the callback on the Fedora Messaging event.

    Attributes:
        msg: Message to be logged in the Fedora Messaging listener.
        pass_to_service: Boolean value that represents whether the event should
            be passed to the worker for further processing or not.

            Defaults to `True`.
    """

    msg: str
    pass_to_service: bool = True


def get_callback(topic: str) -> Callable[[str, dict, str], CallbackResult]:
    return MAPPING.get(topic, _dummy)


def _dummy(topic: str, event: dict, packit_user: str) -> CallbackResult:
    return CallbackResult(
        msg=f"[IGNORE] Unknown message of topic '{topic}'",
        pass_to_service=False,
    )


def _copr(topic: str, event: dict, packit_user: str) -> CallbackResult:
    if event.get("user") != packit_user:
        return CallbackResult(
            msg=f"[Copr] Copr build is not managed by Packit (`{packit_user}`) user.",
            pass_to_service=False,
        )

    return CallbackResult(msg=f"[Copr] {event.get('what')}")


def _koji(topic: str, event: dict, packit_user: str) -> CallbackResult:
    # TODO: accept builds run by other owners as well
    # (For the `bodhi_update` job.)
    if event.get("owner") != packit_user:
        return CallbackResult(
            msg=f"[Koji] Koji build not built by {packit_user}.",
            pass_to_service=False,
        )

    if "buildsys.build.state" in topic:
        what = (
            f"[Koji] build:{event.get('build_id')} task:{event.get('task_id')}"
            f" {event.get('old')}->{event.get('new')}"
        )

    # SAFETY: It's either ‹build.state› or ‹task.state›, as they are the topics
    # handled by this callback, therefore ‹what› **will** be declared one way or
    # another.
    if "buildsys.task.state" in topic:  # scratch build
        what = f"[Koji] id:{event.get('id')} {event.get('old')}->{event.get('new')}"

    return CallbackResult(msg=what)


def _fedora_dg_push(topic: str, event: dict, packit_user: str) -> CallbackResult:
    if getenv("PROJECT", "").startswith("packit") and not specfile_changed(
        event,
    ):
        return CallbackResult(
            msg="[Fedora DG] No specfile change, ignoring the push.",
            pass_to_service=False,
        )

    if commit := event.get("commit"):
        what = f"{commit.get('repo')} {commit.get('rev')}@{commit.get('branch')}"
    else:
        what = "Couldn't get commit out of the event."

    return CallbackResult(msg=f"[Fedora DG] Passing push: {what}")


def _fedora_dg_pr_flag(topic: str, event: dict, packit_user: str) -> CallbackResult:
    if nested_get(event, "pullrequest", "user", "name") != packit_user:
        return CallbackResult(
            msg=f"[Fedora DG] Flag changed in a PR not created by {packit_user}, ignoring.",
            pass_to_service=False,
        )

    return CallbackResult(
        msg=(
            "[Fedora DG] Flag on "
            f"{nested_get(event, 'pullrequest', 'project', 'fullname')}"
            f" changed to '{nested_get(event, 'flag', 'comment')}'"
        ),
    )


def _fedora_dg_pr_comment(topic: str, event: dict, packit_user: str) -> CallbackResult:
    project = nested_get(event, "pullrequest", "project", "fullname")
    comments = nested_get(event, "pullrequest", "comments")
    last_comment = comments[-1]
    return CallbackResult(
        msg=(
            f"[Fedora DG] For {project}"
            f" new comment: '{last_comment['comment']}'"
            f" from {last_comment['user']['name']}"
        ),
    )


def _fedora_dg_pr_closed(topic: str, event: dict, packit_user: str) -> CallbackResult:
    project = nested_get(event, "pullrequest", "project", "fullname")

    if not nested_get(event, "pullrequest", "merged"):
        return CallbackResult(
            msg=f"[Fedora DG] Pull request  in {project} was closed, ignoring.",
            pass_to_service=False,
        )

    return CallbackResult(
        msg=f"[Fedora DG] Merged pull request in {project}.",
    )


def _hotness_bugzilla(topic: str, event: dict, packit_user: str) -> CallbackResult:
    package = event.get("package")
    version = nested_get(event, "trigger", "msg", "project", "version")

    return CallbackResult(
        msg=f"[Hotness] New update of package {package} to version {version}.",
    )


def _anitya_version_update(topic: str, event: dict, packit_user: str) -> CallbackResult:
    pass


# [WARNING]
# When new topics are changed here, then the changes must be also reflected in
# a respective fedora.toml.j2 (https://github.com/packit/deployment/tree/main/secrets)
MAPPING = {
    "org.fedoraproject.prod.copr.build.end": _copr,
    "org.fedoraproject.prod.copr.build.start": _copr,
    "org.fedoraproject.prod.buildsys.task.state.change": _koji,
    "org.fedoraproject.prod.buildsys.build.state.change": _koji,
    "org.fedoraproject.prod.git.receive": _fedora_dg_push,
    "org.fedoraproject.prod.pagure.pull-request.flag.added": _fedora_dg_pr_flag,
    "org.fedoraproject.prod.pagure.pull-request.flag.updated": _fedora_dg_pr_flag,
    "org.fedoraproject.prod.pagure.pull-request.comment.added": _fedora_dg_pr_comment,
    "org.fedoraproject.prod.pagure.pull-request.closed": _fedora_dg_pr_closed,
    "org.fedoraproject.prod.hotness.update.bug.file": _hotness_bugzilla,
    "org.release-monitoring.prod.anitya.project.version.update.v2": _anitya_version_update,
}
