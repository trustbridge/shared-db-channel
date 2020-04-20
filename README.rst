Shared-DB-Channel
==================

This is a simple channel implementation where the channel medium is a shared database.

Development
-----------
Setup project (copy .env_sample to .env)::

	./pie.py setup

To (re-)build the service::

	./pie.py build

To run the service execute the following command::

	./pie.py start

To run tests::

	./pie.py test

To start service using DB instance running on your host machine. Use env to setup DB connection (or .env)::

	DB_HOST=localhost DB_PORT=5432 ./pie.py start_channel_api

To generate API spec::

	./pie.py generate_swagger
