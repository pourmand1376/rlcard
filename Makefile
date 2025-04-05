export PYTHONPATH := $(CURDIR):$(PYTHONPATH)

.PHONY: all test examples

all: test examples

test:
	python3 -m pytest tests/

examples:
	python3 examples/blackjack_dqn.py
	# Add other example commands as needed


