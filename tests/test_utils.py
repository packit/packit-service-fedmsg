# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest

from packit_service_fedmsg.utils import specfile_changed


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param(
            {"changed_files": {"nispor.spec": "M"}},
            True,
        ),
        pytest.param(
            {"changed_files": {"README.packit": "M", "nispor.spec": "M"}},
            True,
        ),
        pytest.param({}, False),
        pytest.param(
            {
                "changed_files": {"README.md": "M"},
            },
            False,
        ),
        pytest.param(
            {
                "changed_files": {},
            },
            False,
        ),
    ],
)
def test_specfile_changed(body, expected):
    assert specfile_changed(body) == expected
