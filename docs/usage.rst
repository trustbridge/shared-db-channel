Usage
=====

The Shared DB Channel is a simplistic, non-blockchain implementation of an IGL Node. Due to its non-distributed nature (the "channel medium" is a central, shared DB),
it is only intended for use in development situations.


WIP Process
-----------

Env vars are hardcoded into pie_tasks

Start the shared db and create the schema

.. code::

   pie shared_db.destroy
   pie shared_db.start
   # other tasks useful for dev: logs, show_env
   pie api.build
   pie api.upgrade_db_schema


Start the api endpoint

.. code::

   pie api.build
   pie api.start


Next step, extract env vars from pie_tasks and put env files (cross platform compatible) for various instances together and make them simple to run. Eg. so that you could run a single extra command/set a single environment variable to select the configuration required and spin up an instance:

.. code::

   set SHARED_DB_INSTANCE=AU_SG_CHANNEL_AU_ENDPOINT
   # this shouldn't be required for api.build, but I think it currently is as it needs a valid yml file
   pie api.start

   set SHARED_DB_INSTANCE=AU_SG_CHANNEL
   pie.shared_db.start

   This also needs to maintain docker-compose separation (setting COMPOSE_PROJECT_NAME should do this; perhaps we continue to use this to select the instance)


Quick Start
-----------

The simplest case is that you want to start a single shared DB and create one endpoint that interacts with it. This will let you test posting messages through a node.

.. code::

   pie db.default.start
   pie api.au.start


The next simplest case would be to spin up a second endpoint on the foreign side. This will let you test the foreign node receiving messages you posted and let you post messages from a foreign node and receive them back on your local node.

.. code::

   pie db.default.start
   pie api.au.start
   pie api.sg.start


The more complex, real world scenario is to spin up multiple DBs, each with several endpoints interacting with them. To do this, you will have to specify port numbers and connection strings as environment variables.

.. code::

   SHARED_DB_PORT=xxxx
   pie db.start

   SHARED_DB_CONNECTION_STRING=postgres::/...
   API_PORT=xxxx
   API_COUNTRY=NZ
   pie api.start

   SHARED_DB_CONNECTION_STRING=postgres::/...
   API_PORT=xxxx
   API_COUNTRY=NZ
   pie api.start



Architecture
------------

.. uml::

   @startuml
   caption High level channel architecture

   [Intergov Node 1] as intergov_node_1
   [Intergov Node 2] as intergov_node_2
   [Intergov Node 3] as intergov_node_3

   package "Channel" {
      [<<Flask API>>\nChannel Endpoint 1] as channel_endpoint_1
      [<<Flask API>>\nChannel Endpoint 2] as channel_endpoint_2
      [<<Flask API>>\nChannel Endpoint 3] as channel_endpoint_3
      Database "<<PostgreSQL DB>>\nChannel Medium" as channel_medium
   }

   intergov_node_1 <--> channel_endpoint_1
   intergov_node_2 <-- channel_endpoint_2
   intergov_node_3 --> channel_endpoint_3
   channel_endpoint_1 <--> channel_medium
   channel_endpoint_2 <-- channel_medium
   channel_endpoint_3 --> channel_medium
   @enduml
