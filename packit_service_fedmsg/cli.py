# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Listen to messages coming to fedora-messaging (AMQP)
"""

import click

from packit_service_fedmsg.consumer import Consumerino


@click.command("listen-to-fedora-messaging")
def listen_to_fedora_messaging():
    """
    Listen to events on fedora messaging and process them.
    """

    consumerino = Consumerino()
    consumerino.consume_from_fedora_messaging()
