Shared-DB-Channel
==================

This is a simple channel implementation where the channel medium is a shared database.

Development
-----------

To run the service execute the following command::

	docker-compose up


To run tests::

	docker-compose run api pytest


To start service using DB instance running on your host machine::

	docker-compose -f ./docker-compose-shared-db.yml up
