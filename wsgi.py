#!/usr/bin/python
import os

from setings import env

for k, v in env:
    os.environ[k] = v


from mkopen.app import create_app

application = create_app()
