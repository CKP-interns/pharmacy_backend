#!/bin/bash
# Azure App Service startup script for Django
cd /home/site/wwwroot
gunicorn pharmacy_backend.wsgi --bind=0.0.0.0 --timeout 600

