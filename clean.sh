#!/bin/sh
find . -name '*.pyc' | xargs rm
find . -name '*~' | xargs rm
