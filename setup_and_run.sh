#!/bin/bash
# Setup and run script for Academie Numerique

echo "=== Setting up Academie Numerique ==="

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py makemigrations videoconf
python manage.py migrate

# Create superuser if needed
echo "Creating superuser (if not exists)..."
python manage.py createsuperuser --noinput --email admin@test.com --username admin 2>/dev/null || echo "Superuser may already exist"

# Start the server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
