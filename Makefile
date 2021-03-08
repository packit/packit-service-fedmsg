IMAGE ?= quay.io/packit/packit-service-fedmsg:dev
CONTAINER_ENGINE ?= docker
ANSIBLE_PYTHON ?= /usr/bin/python3
AP ?= ansible-playbook -vv -c local -i localhost, -e ansible_python_interpreter=$(ANSIBLE_PYTHON)

build: files/install-deps.yaml files/recipe.yaml
	$(CONTAINER_ENGINE) build --rm -t $(IMAGE) .

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
