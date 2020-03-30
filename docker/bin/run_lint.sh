docker-compose up -d --build
docker-compose exec server bash -c "./bin/pylint.sh"
docker-compose down
