FROM quay.io/packit/base:c9s

ENV USER=packit \
    HOME=/home/packit \
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
