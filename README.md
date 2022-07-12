# Fedora messaging consumer for Packit Service

This component of [Packit Service](https://packit.dev/packit-as-a-service) listens on [Fedora's messaging](https://fedora-messaging.readthedocs.io) AMPQ broker and sends Celery tasks to [Packit Service worker](https://github.com/packit-service/packit-service/tree/main/packit_service/worker).

- Our website: [packit.dev](https://packit.dev)
- [CONTRIBUTING.md](/CONTRIBUTING.md)

## bindings

When new routes (like `org.fedoraproject.prod.pagure.pull-request.comment.added`) are added/removed here then they must be added/removed also in [fedora.toml](https://github.com/packit/deployment/tree/main/secrets#what-secret-files-the-deployment-expects) in Bitwarden following the [routing_key docs](https://fedora-messaging.readthedocs.io/en/stable/configuration.html#bindings).
