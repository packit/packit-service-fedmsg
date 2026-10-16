# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import json

import pytest

from packit_service_fedmsg.utils import specfile_changed
from tests.spellbook import DATA_DIR


def forgejo_dg_push_spec_changed_json():
    with open(DATA_DIR / "forgejo_dg_push_spec_changed.json") as outfile:
        json_msg = json.load(outfile)

    return json_msg["body"]


@pytest.mark.parametrize(
    ("topic", "body", "expected"),
    [
        pytest.param(
            "org.fedoraproject.prod.pagure.git.receive",
            {"changed_files": {"nispor.spec": "M"}},
            True,
        ),
        pytest.param(
            "org.fedoraproject.prod.pagure.git.receive",
            {"changed_files": {"README.packit": "M", "nispor.spec": "M"}},
            True,
        ),
        pytest.param("org.fedoraproject.prod.pagure.git.receive", {}, False),
        pytest.param(
            "org.fedoraproject.prod.pagure.git.receive",
            {
                "changed_files": {"README.md": "M"},
            },
            False,
        ),
        pytest.param(
            "org.fedoraproject.prod.pagure.git.receive",
            {
                "changed_files": {},
            },
            False,
        ),
        pytest.param(
            "org.fedoraproject.prod.forgejo.push",
            forgejo_dg_push_spec_changed_json(),
            True,
        ),
    ],
)
def test_specfile_changed(topic, body, expected):
    assert specfile_changed(topic, body) == expected
