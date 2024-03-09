# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import json

from celery import Celery
from fedora_messaging import message
from flexmock import flexmock

from packit_service_fedmsg.consumer import Consumerino
from tests.spellbook import DATA_DIR


def test_build_state_change_not_build_method():
    flexmock(Celery).should_receive("send_task").never()
    with open(DATA_DIR / "koji_build_state_change.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])
