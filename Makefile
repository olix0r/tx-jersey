# jersey core lib makefile
# Copyright 2009 Yahoo!, Inc.  All rights reserved.

PYTHON ?=	python2.6
TRIAL ?=	trial
TRIAL_ENV=	PYTHONPATH=build/lib:${PYTHONPATH}
TRIAL_ARGS?=	--coverage
TRIAL_REPORTER?= verbose
TRIAL_EXEC=	env ${TRIAL_ENV} ${TRIAL} --reporter=${TRIAL_REPORTER} ${TRIAL_ARGS}


help:
	@echo "Targets: build,"
	@echo "         package,"
	@echo "         clean, clean-dist, clean-test"
	@echo "         test, test-cli, test-inet, test-log"


package:
	${PYTHON} setup.py bdist


build:
	${PYTHON} setup.py build


test: test-all

test-all: build
	${TRIAL_EXEC} jersey.cases

test-cli: build
	${TRIAL_EXEC} jersey.cases.test_cli

test-inet: build
	${TRIAL_EXEC} jersey.cases.test_inet

test-log: build
	${TRIAL_EXEC} jersey.cases.test_log


clean-all: clean clean-test clean-dist

clean:
	${PYTHON} setup.py clean -a
	rm -rf build

clean-test:
	rm -rf _trial_temp*

clean-dist:
	rm -rf dist


