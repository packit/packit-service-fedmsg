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
    if "buildsys.tag" in topic:
        if "-side-" not in event.get("tag"):
            # consider only tagging into sidetags
            return CallbackResult(
                msg="[Koji] Koji build not tagged into a sidetag.",
                pass_to_service=False,
            )

        what = f"[Koji] build:{event.get('build_id')} tag:{event.get('tag')}"
        return CallbackResult(msg=what)

    if "buildsys.build.state" in topic:
        if nested_get(event, "task", "method") != "build":
            return CallbackResult(
                msg="[Koji] Koji build with method other than 'build'.",
                pass_to_service=False,
            )

        if event.get("owner") == "releng":
            return CallbackResult(
                msg="[Koji] Koji build built by 'releng'.",
                pass_to_service=False,
            )

        what = (
            f"[Koji] build:{event.get('build_id')} task:{event.get('task_id')}"
            f" {event.get('old')}->{event.get('new')}"
        )
        return CallbackResult(msg=what)

    # for scratch builds, consider only builds by packit
    if event.get("owner") != packit_user:
        return CallbackResult(
            msg=f"[Koji] Koji scratch build not built by {packit_user}.",
            pass_to_service=False,
        )

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

    repo_name = nested_get(event, "repo", "name")

    what = f"{repo_name} {event.get('end_commit')}@{event.get('branch')}"

    return CallbackResult(msg=f"[Fedora DG] Passing push: {what}")


def _fedora_dg_pr_new(topic: str, event: dict, packit_user: str) -> CallbackResult:
    return CallbackResult(
        msg=(
            f"[Fedora DG] PR #{nested_get(event, 'pullrequest', 'id')} opened in "
            f"{nested_get(event, 'pullrequest', 'project', 'fullname')}"
        ),
    )


def _fedora_dg_pr_updated(topic: str, event: dict, packit_user: str) -> CallbackResult:
    return CallbackResult(
        msg=(
            f"[Fedora DG] PR #{nested_get(event, 'pullrequest', 'id')} updated in "
            f"{nested_get(event, 'pullrequest', 'project', 'fullname')}"
        ),
    )


def _fedora_dg_pr_rebased(topic: str, event: dict, packit_user: str) -> CallbackResult:
    return CallbackResult(
        msg=(
            f"[Fedora DG] PR #{nested_get(event, 'pullrequest', 'id')} rebased in "
            f"{nested_get(event, 'pullrequest', 'project', 'fullname')}"
        ),
    )


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
    package = None
    for p in nested_get(event, "message", "packages"):
        if p.get("distro") == "CentOS":
            package = p.get("package_name")
            break

    if package is None:
        project = nested_get(event, "project", "name")
        return CallbackResult(
            msg=f"[Anitya] CentOS mapping is not configured for {project}, ignoring.",
            pass_to_service=False,
        )

    new_versions = nested_get(event, "message", "upstream_versions")

    return CallbackResult(
        msg=f"[Anitya] New versions of package {package}: '{', '.join(new_versions)}'",
    )


def _openscanhub_task_finished(
    topic: str,
    event: dict,
    packit_user: str,
) -> CallbackResult:
    return CallbackResult(
        msg=f"[OpenScanHub] OpenScanHub task {event.get('task_id')} "
        f"finished with status {event.get('status')}: "
        f"added.js={event.get('added.js')}, fixed.js={event.get('fixed.js')}.",
    )


def _openscanhub_task_started(
    topic: str,
    event: dict,
    packit_user: str,
) -> CallbackResult:
    return CallbackResult(
        msg=f"[OpenScanHub] OpenScanHub task {event.get('task_id')} started.",
    )


# [WARNING]
# Configuration of the topics to listen to needs to be changed in
# a respective fedora.toml.j2 (https://github.com/packit/deployment/tree/main/secrets)
MAPPING = {
    "org.fedoraproject.prod.copr.build.end": _copr,
    "org.fedoraproject.prod.copr.build.start": _copr,
    "org.fedoraproject.prod.buildsys.task.state.change": _koji,
    "org.fedoraproject.prod.buildsys.build.state.change": _koji,
    "org.fedoraproject.prod.buildsys.tag": _koji,
    "org.fedoraproject.prod.pagure.git.receive": _fedora_dg_push,
    "org.fedoraproject.prod.pagure.pull-request.new": _fedora_dg_pr_new,
    "org.fedoraproject.prod.pagure.pull-request.updated": _fedora_dg_pr_updated,
    "org.fedoraproject.prod.pagure.pull-request.rebased": _fedora_dg_pr_rebased,
    "org.fedoraproject.prod.pagure.pull-request.flag.added": _fedora_dg_pr_flag,
    "org.fedoraproject.prod.pagure.pull-request.flag.updated": _fedora_dg_pr_flag,
    "org.fedoraproject.prod.pagure.pull-request.comment.added": _fedora_dg_pr_comment,
    "org.fedoraproject.prod.pagure.pull-request.closed": _fedora_dg_pr_closed,
    "org.fedoraproject.prod.hotness.update.bug.file": _hotness_bugzilla,
    "org.release-monitoring.prod.anitya.project.version.update.v2": _anitya_version_update,
    "org.fedoraproject.prod.openscanhub.task.started": _openscanhub_task_started,
    "org.fedoraproject.prod.openscanhub.task.finished": _openscanhub_task_finished,
}
