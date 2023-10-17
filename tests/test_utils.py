# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest

from packit_service_fedmsg.utils import specfile_changed


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param(
            {
                "commit": {
                    "stats": {
                        "files": {
                            ".gitignore": {"additions": 1, "deletions": 0, "lines": 1},
                            "buildah.spec": {
                                "additions": 5,
                                "deletions": 2,
                                "lines": 7,
                            },
                            "sources": {"additions": 1, "deletions": 1, "lines": 2},
                        },
                        "total": {
                            "additions": 7,
                            "deletions": 3,
                            "files": 3,
                            "lines": 10,
                        },
                    },
                    "summary": "buildah-1.12.0-0.73.dev.git1e6a70c",
                    "username": "rhcontainerbot",
                },
            },
            True,
        ),
        pytest.param(
            {
                "commit": {
                    "stats": {
                        "files": {
                            ".gitignore": {"additions": 1, "deletions": 0, "lines": 1},
                            "sources": {"additions": 1, "deletions": 1, "lines": 2},
                        },
                        "total": {
                            "additions": 7,
                            "deletions": 3,
                            "files": 3,
                            "lines": 10,
                        },
                    },
                    "summary": "buildah-1.12.0-0.73.dev.git1e6a70c",
                    "username": "rhcontainerbot",
                },
            },
            False,
        ),
        pytest.param({}, False),
        pytest.param(
            {
                "commit": {
                    "stats": {},
                    "summary": "buildah-1.12.0-0.73.dev.git1e6a70c",
                    "username": "rhcontainerbot",
                },
            },
            False,
        ),
        pytest.param(
            {
                "commit": {},
            },
            False,
        ),
    ],
)
def test_specfile_changed(body, expected):
    assert specfile_changed(body) == expected
