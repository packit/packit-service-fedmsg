# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from typing import Any
from urllib.parse import urlparse

from packit_service_fedmsg.constants import FEDORA_DIST_GIT_HOSTNAMES


def nested_get(d: dict, *keys, default=None) -> Any:
    """
    Recursively obtain value from nested dict.

    Args:
        d: Dictionary to get value from.
        keys: Path within the dictionary.
        default: Value to be returned if some key is not found.

            Defaults to `None`.

    Returns:
        Value found in the dictionary or specified default.
    """
    response = d

    try:
        for k in keys:
            response = response[k]
    except (KeyError, AttributeError, TypeError):
        # logger.debug("can't obtain %s: %s", k, ex)
        return default

    return response


def specfile_changed(body: dict) -> bool:
    """
    Does the commit contain specfile change?

    Args:
        body: Body of the message.

    Returns:
        `True` if the specfile has changed, `False` otherwise.
    """
    files = body.get("changed_files")
    file_names = files.keys() if files else []

    return any(file_name.endswith(".spec") for file_name in file_names)


def is_fedora_dist_git_url(url: str) -> bool:
    """
    Does the specified url belong to Fedora dist-git?

    Args:
        url: Repo url

    Returns:
        `True` if url belongs to Fedora dist-git, `False` otherwise.
    """
    if not url:
        return False

    return any(
        hostname == urlparse(url).hostname for hostname in FEDORA_DIST_GIT_HOSTNAMES
    )
