include common.mk

PYTHONPATH = $(PWD)
export PYTHONPATH

test:
	python -m doctest ffcrunch/*.py
	$(MAKE) -C test/ test

.PHONY: test
