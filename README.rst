.. image:: https://travis-ci.org/ome/omero-mapr.svg?branch=master
    :target: https://travis-ci.org/ome/omero-mapr

.. image:: https://gitlab.com/aleksandra-tarkowska/mapr/badges/master/build.svg
    :target: https://gitlab.com/aleksandra-tarkowska/mapr/commits/master

.. image:: https://badge.fury.io/py/omero-mapr.svg
    :target: https://badge.fury.io/py/omero-mapr


MAPR
====

An OMERO.web app allowing to browse the data through attributes linked to the image

Requirements
============

* OMERO 5.3 or newer.

Installing from Pypi
====================

This section assumes that an OMERO.web is already installed.

Install the app using `pip <https://pip.pypa.io/en/stable/>`_:

::

    $ pip install omero-mapr

plug in the app to OMERO.web

::

    $ bin/omero config append omero.web.apps '"omero_mapr"'

    $ bin/omero config append omero.web.ui.top_links '["Key1", {"viewname": "maprindex_key1", "query_string": {"experimenter": -1}}, {"title": "Key1 browser"}]'

    $ bin/omero config append omero.web.mapr.config '{"menu": "key1", "config": {"default": ["Key1"], "all": ["Key1", "Key2"], "ns": ["openmicroscopy.org/mapr/key1"], "label": "Key1"}}'


Now restart OMERO.web as normal.

Testing
=======

Testing MAPR requires OMERO.server running.
Run tests (includes self-contained OMERO.server, requires docker)::

    docker-compose -f docker/docker-compose.yml up --build --abort-on-container-exit
    docker-compose -f docker/docker-compose.yml rm -fv

Run test against remote server::

    ./runtest $host $port

License
-------

MAPR is released under the AGPL.


Copyright
---------

2016, The Open Microscopy Environment
