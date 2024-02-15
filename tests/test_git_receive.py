import json

from celery import Celery
from fedora_messaging import message
from flexmock import flexmock

from packit_service_fedmsg.consumer import Consumerino
from tests.spellbook import DATA_DIR


def test_git_receive():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "git_receive.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])
