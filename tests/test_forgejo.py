# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import json

from celery import Celery
from fedora_messaging import message
from flexmock import flexmock

from packit_service_fedmsg.consumer import Consumerino
from tests.spellbook import DATA_DIR


def test_dg_push_event():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "forgejo_dg_push.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])


def test_dg_pull_request_event():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "forgejo_dg_pr.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])


def test_dg_issue_comment_event():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "forgejo_dg_issue_comment.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])


def test_dg_pr_comment_event():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "forgejo_dg_pr_comment.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])


def test_dg_action_run_event():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "forgejo_dg_action_run.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])


def test_reject_upstream_event():
    flexmock(Celery).should_receive("send_task").never()
    with open(DATA_DIR / "forgejo_upstream_push.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])
