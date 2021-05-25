# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

IMAGE ?= quay.io/packit/packit-service-fedmsg:dev
CONTAINER_ENGINE ?= $(shell command -v podman 2> /dev/null || echo docker)
ANSIBLE_PYTHON ?= /usr/bin/python3
AP ?= ansible-playbook -vv -c local -i localhost, -e ansible_python_interpreter=$(ANSIBLE_PYTHON)
TEST_IMAGE := fedmsg-test
TEST_TARGET := ./tests/

build: files/install-deps.yaml files/recipe.yaml
	$(CONTAINER_ENGINE) build --rm -t $(IMAGE) .

build-test-image: build
	$(CONTAINER_ENGINE) build --rm -t $(TEST_IMAGE) -f Containerfile.tests .

# run 'make build' first
# copy (symlink) fedora.toml from our packit-service@gitlab repo into this dir
run:
	$(CONTAINER_ENGINE) run --rm \
	    --env FEDORA_MESSAGING_CONF=/home/packit/.config/fedora.toml \
	    --env REDIS_SERVICE_HOST=redis \
        -v $(CURDIR)/packit_service_fedmsg:/usr/local/lib/python3.7/site-packages/packit_service_fedmsg \
        -v $(CURDIR)/fedora.toml:/home/packit/.config/fedora.toml \
        --security-opt label=disable \
		$(IMAGE)

check:
	find . -name "*.pyc" -exec rm {} \;
	PYTHONPATH=$(CURDIR) PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --verbose --showlocals  $(TEST_TARGET)

check-in-container:
	$(CONTAINER_ENGINE) run --rm -it -v $(CURDIR):/src:Z -w /src $(TEST_IMAGE) make check

.PHONY: run check install-check-deps install-check-in-container-deps check-in-container
