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


Subscriptions
-------------

Assuming you have Australian intergov started locally as it's stated in the readme

To subscribe to all messages for the jurisdiction::

    curl -v -XPOST \
        http://localhost:8180/messages/subscriptions/by_jurisdiction \
        -d 'hub.topic=AU&hub.callback=http://172.17.0.1:5009/channel-message&hub.mode=subscribe'
