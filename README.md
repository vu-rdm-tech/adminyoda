# Yoda administration database

A simple implementation of a "shadow database" to store administrative information and generate usage reports.

To set up a dev environment:
- rename .env.template to .env and set suitable values
- Build and startup with docker
```
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up
```
- Open http://localhost:8080
