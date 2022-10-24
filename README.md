# Fedora messaging consumer for Packit Service

This component of [Packit Service](https://packit.dev/packit-as-a-service) listens on [Fedora's messaging](https://fedora-messaging.readthedocs.io) AMPQ broker and sends Celery tasks to [Packit Service worker](https://github.com/packit-service/packit-service/tree/main/packit_service/worker).

- Our website: [packit.dev](https://packit.dev)
- [CONTRIBUTING.md](/CONTRIBUTING.md)

## bindings

When new routes (like e.g. `org.fedoraproject.prod.pagure.pull-request.comment.added`)
are added/removed [here](packit_service_fedmsg/consumer.py) then they must be added/removed also in
respective [fedora.toml.j2](https://github.com/packit/deployment/tree/main/secrets)
following the [routing_keys docs](https://fedora-messaging.readthedocs.io/en/stable/configuration.html#bindings).
