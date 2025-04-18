.PHONY: help
help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

export PYTHONPATH := $(CURDIR):$(PYTHONPATH)

.PHONY: all test examples install-dev play-hokm

all: test examples

test: ## run tests
	python3 -m pytest tests/

examples: ## run examples
	python3 examples/blackjack_dqn.py
	# Add other example commands as needed

install-dev: ## install for development
	pip install -e $(CURDIR)

play-hokm: install-dev ## play hokm with visual display of cards on the table
	python examples/human/hokm_human.py


