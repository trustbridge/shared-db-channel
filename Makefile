build:
	docker-compose build api

run:
	docker-compose up

run-shared-db:
	docker-compose -f ./docker-compose-shared-db.yml up

test:
	docker-compose run tests

docs:
	docker-compose run api python ./manage.py generate_swagger
