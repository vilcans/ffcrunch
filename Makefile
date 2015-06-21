include common.mk

PYTHONPATH = $(PWD)
export PYTHONPATH

test:
	$(MAKE) -C test/ test

.PHONY: test
