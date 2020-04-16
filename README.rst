Shared-DB-Channel
==================

This is a simple channel implementation where the channel medium is a shared database.

Development
-----------

To (re-)build the service::

	docker-compose build

To run the service execute the following command::

	docker-compose up

To run tests::

	docker-compose run api pytest

To start service using DB instance running on your host machine::

	docker-compose -f ./docker-compose-shared-db.yml up

To generate API spec::

	docker-compose run api python ./manage.py generate_swagger
