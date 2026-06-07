#!/usr/bin/env bash
# Render runs this script every time you deploy.
# exit immediately if any command fails
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect all static files (CSS, JS) into /staticfiles for WhiteNoise to serve
python manage.py collectstatic --no-input

# Apply any pending database migrations
python manage.py migrate
