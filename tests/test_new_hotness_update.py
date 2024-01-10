import json

from celery import Celery
from fedora_messaging import message
from flexmock import flexmock

from packit_service_fedmsg.consumer import Consumerino
from tests.spellbook import DATA_DIR


def test_new_hotness_reaction():
    flexmock(Celery).should_receive("send_task").and_return(flexmock(id="a")).once()
    with open(DATA_DIR / "new_hotness_update.json") as outfile:
        json_msg = json.load(outfile)
        msg = message.loads(json.dumps(json_msg))
        c = Consumerino()
        c(msg[0])
