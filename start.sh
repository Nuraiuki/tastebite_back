#!/bin/bash

# start.sh
flask db upgrade
exec gunicorn wsgi:app
