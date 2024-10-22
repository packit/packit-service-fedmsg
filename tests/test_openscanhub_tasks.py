# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import json

from celery import Celery
from fedora_messaging import message
from flexmock import flexmock

from packit_service_fedmsg.consumer import Consumerino
from tests.spellbook import DATA_DIR


def test_tasks_events():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).twice()
    for event in ["openscanhub_task_finished", "openscanhub_task_started"]:
        with open(DATA_DIR / f"{event}.json") as outfile:
            json_msg = json.load(outfile)
            msg = message.loads(json.dumps(json_msg))
            c = Consumerino()
            c(msg[0])
