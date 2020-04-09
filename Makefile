run:
	docker-compose up

run-shared-db:
	docker-compose -f ./docker-compose-shared-db.yml up

test:
	docker-compose run api pytest

