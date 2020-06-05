Development
===========

TODO: came from readme, to be merged into usage, I think


Setup project (copy .env_sample to .env)::

   ./pie.py setup

Detailed information about the purpose of each env variable can be found in .env_sample

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
