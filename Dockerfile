FROM quay.io/packit/base:c9s
# [NOTE] Adjust ‹PYTHONPATH› when changing the default image

ENV USER=packit \
    HOME=/home/packit \
    # [NOTE] Fixes the issue with importing after upgrading Fedora Messaging to
    # 3.5.0: fedora-infra/fedora-messaging#364
    PYTHONPATH="/usr/local/lib/python3.9/site-packages"

COPY files/install-deps.yaml /src/files/
RUN cd /src/ \
    && ansible-playbook -vv -c local -i localhost, files/install-deps.yaml \
    && dnf clean all

COPY setup.py setup.cfg files/recipe.yaml files/liveness.sh /src/
# setuptools-scm
COPY .git /src/.git
COPY packit_service_fedmsg/ /src/packit_service_fedmsg/

RUN cd /src/ \
    && ansible-playbook -vv -c local -i localhost, recipe.yaml \
    && rm -rf /src/

CMD ["fedora-messaging", "consume", "--callback=packit_service_fedmsg.consumer:Consumerino"]
