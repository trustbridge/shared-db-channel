Overview
========

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


.. graphviz:: channel_infrastructure.dot


See :doc:`development` for instructions on how to spin up instances locally.
