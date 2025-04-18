export PYTHONPATH := $(CURDIR):$(PYTHONPATH)

.PHONY: all test examples install-dev play-hokm

all: test examples

test:
	python3 -m pytest tests/

examples:
	python3 examples/blackjack_dqn.py
	# Add other example commands as needed

install-dev:
	pip install -e $(CURDIR)

play-hokm: install-dev
	python examples/human/hokm_human.py


