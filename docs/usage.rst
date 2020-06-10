Usage
=====

The Shared DB Channel is a simplistic, non-blockchain implementation of an IGL Node. Due to its non-distributed nature
(the "channel medium" is a central, shared DB), it is only intended for use in development situations.


Architecture
------------

A shared database is used by multiple channel endpoints:

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
      Database "<<PostgreSQL DB>>\nChannel Medium\nShared DB" as channel_medium
   }

   intergov_node_1 <--> channel_endpoint_1
   intergov_node_2 <-- channel_endpoint_2
   intergov_node_3 --> channel_endpoint_3
   channel_endpoint_1 <--> channel_medium
   channel_endpoint_2 <-- channel_medium
   channel_endpoint_3 --> channel_medium
   @enduml


Each instance of a shared DB channel has one PostgreSQL DB and 2 or more channel endpoints.
A separate channel would have its own instance of the shared DB and its own instances of channel endpoints.

.. uml::

   @startuml
   caption Instance of a single channel endpoint

   package "Channel Endpoint" {
      [<<Flask API>>\nChannel Endpoint API] as api
      [<<Minio>>\nSubscription Store] as subscription_store
      [<<ElasticMQ>>\nSubscription Event Queue] as subscription_event_queue
   }
   Database "<<PostgreSQL DB>>\nChannel Medium\nShared DB" as channel_medium

   api <--> channel_medium
   @enduml


Instances can be spun up quickly using docker-compose. ``COMPOSE_PROJECT_NAME`` is used to select the instance to run.

In the ``docker`` folder, there are ``.env`` files to configure particular instances of the components.

 - ``api.env`` contains settings that apply to ALL instances of the channel endpoint API.
 - ``api_<COMPOSE_PROJECT_NAME>.env`` contains settings specific to that channel endpoint API instance.
 - ``api_<COMPOSE_PROJECT_NAME>_local.env`` is missing but can override settings from the other two files for your specific local needs.

The same structure is used for the ``shared_db`` component. ``shared_db.env``, ``shared_db_<COMPOSE_PROJECT_NAME>.env`` and ``shared_db_<COMPOSE_PROJECT_NAME>_local.env``.

All ``api_*_local.env`` and ``shared_db_*_local.env`` files are .gitignored.


Dev Instances
-------------

An AU-SG channel can be run with:

.. code::

   export/set COMPOSE_PROJECT_NAME=au_sg_channel
   pie shared_db.destroy
   pie shared_db.start
   # other tasks useful for dev: logs, show_env

   # TODO: remove dependence on the API for creation of the schema
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
   pie api.build
   pie api.upgrade_db_schema

   # and start the AU API endpoint
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
   pie api.build
   pie api.start
   # http://localhost:8180
   # other tasks: stop, destroy, test, generate_swagger

   # and start the SG API endpoint
   export/set COMPOSE_PROJECT_NAME=au_sg_channel_sg_endpoint
   pie api.start
   # http://localhost:8181