Development
===========

Config exists in the repo to start an AU-SG channel locally using docker-compose. ``COMPOSE_PROJECT_NAME`` is used to select the instance to run.


Config
------

In the ``docker`` folder, there are ``.env`` files to configure particular instances of the components.

 - ``api.env`` contains settings that apply to ALL instances of the channel endpoint API.
 - ``api_<COMPOSE_PROJECT_NAME>.env`` contains settings specific to that channel endpoint API instance.
 - ``api_<COMPOSE_PROJECT_NAME>_local.env`` is missing but can override settings from the other two files for your specific local needs.

The same structure is used for the ``shared_db`` component. ``shared_db.env``, ``shared_db_<COMPOSE_PROJECT_NAME>.env`` and ``shared_db_<COMPOSE_PROJECT_NAME>_local.env``.

All ``api_*_local.env`` and ``shared_db_*_local.env`` files are .gitignored.


Instructions
------------

Depending on how you have configured your command line, you may need to substitute ``pie`` below for ``./pie.py`` or ``python3 pie.py``

Start the AU-SG shared DB:

.. code::

   # select the shared_db config for the au_sg_channel
   export/set COMPOSE_PROJECT_NAME=au_sg_channel
   # optionally destroy everything for the shared_db first
   pie shared_db.destroy
   pie shared_db.start
   # to reset the database without rebuilding images
   pie api.stop api.reset api.start
   # other tasks useful for dev: shared_db.logs, shared_db.show_env

Build the API images:

.. code::

   # optionally destroy everything for the api first
   pie api.destroy
   # build the api images
   pie api.build

Complete the shared DB startup by running database migrations:

.. code::

   # use one of the api containers to upgrade the shared_db schema
   # TODO: remove dependence on the API for creation of the schema
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
   pie api.upgrade_db_schema

Start the AU endpoint:

.. code::

   # start the AU API endpoint
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
   pie api.start
   # http://localhost:8180
   # to reset the api (eg. subscriptions) without rebuilding images
   pie api.stop api.reset api.start
   # other tasks: api.logs, api.docker_compose_config

And start the SG endpoint:

.. code::

   # and start the SG API endpoint
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_sg_endpoint
   pie api.start
   # http://localhost:8181
   # everything above about the AU API endpoint also applies to the SG API endpoint

To generate the API spec:

.. code::

   pie api.generate_swagger


Testing
-------

To run tests

.. code::

   export/set COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
   pie api.test

To start the service using a DB instance running on your host machine, override the ``DATABASE_URI`` env var in your relevant ``api-*-local.env`` file.


Subscriptions
-------------

Assuming you have Australian intergov started locally as it's stated in the readme

To subscribe to all messages for the jurisdiction::

    curl -v -XPOST \
        http://localhost:8180/messages/subscriptions/by_jurisdiction \
        -d 'hub.topic=AU&hub.callback=http://172.17.0.1:5009/channel-message&hub.mode=subscribe'
