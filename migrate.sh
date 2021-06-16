#!/bin/bash
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python3 manage.py showmigrations"
docker-compose -f docker-compose-prod.yml exec -T web bash -c "python3 manage.py migrate"
