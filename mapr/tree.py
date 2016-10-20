#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>,
#
# Version: 1.0

import logging
import omero

from omero.rtypes import rstring, rlist, unwrap, wrap
from django.conf import settings
from copy import deepcopy

from omeroweb.webclient.tree import build_clause
from omeroweb.webclient.tree import parse_permissions_css
from omeroweb.webclient.tree import _marshal_screen
from omeroweb.webclient.tree import _marshal_plate
from omeroweb.webclient.tree import _marshal_image
from omeroweb.webclient.tree import _marshal_annotation, _marshal_exp_obj


logger = logging.getLogger(__name__)


def _set_parameters(mapann_ns=[], mapann_names=[],
                    mapann_query=None, mapann_value=None,
                    params=None, experimenter_id=-1,
                    page=1, limit=settings.PAGE):
    if params is None:
        params = omero.sys.ParametersI()

    # Paging
    if page is not None and page > 0:
        params.page((page-1) * limit, limit)

    where_clause = []

    if mapann_names is not None and len(mapann_names) > 0:
        manlist = [rstring(str(n)) for n in mapann_names]
        params.add("filter", rlist(manlist))
        where_clause.append('mv.name in (:filter)')

    if mapann_ns is not None and len(mapann_ns) > 0:
        mnslist = [rstring(str(n)) for n in mapann_ns]
        params.add("ns", rlist(mnslist))
        where_clause.append('a.ns in (:ns)')

    if experimenter_id is not None and experimenter_id != -1:
        params.addId(experimenter_id)
        where_clause.append('a.details.owner.id = :id')

    if mapann_query:
        # query starts from search terms
        params.addString(
            "query",
            rstring("%%%s%%" % str(mapann_query).lower()))
        where_clause.append('lower(mv.value) like :query')

    if mapann_value:
        params.addString("value", mapann_value)
        where_clause.append('mv.value  = :value')

    return params, where_clause


def _marshal_map(conn, row):
    ''' Given a Map row (list) marshals it into a dictionary.  Order
        and type of columns in row is:
          * id (rlong)
          * value (rstring)
          * description (rstring)
          * details.owner.id (rlong)
          * details.permissions (dict)
          * namespace (rstring)

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param row The Tag row to marshal
        @type row L{list}

    '''
    map_id, value, description, owner_id, permissions, namespace, \
        child_count = row

    mapann = dict()
    mapann['id'] = unwrap(map_id)
    mapann['name'] = unwrap(value)
    desc = unwrap(description)
    if desc:
        mapann['description'] = desc
    mapann['ownerId'] = unwrap(owner_id)
    mapann['permsCss'] = parse_permissions_css(permissions,
                                               unwrap(owner_id), conn)

    mapann['childCount'] = unwrap(child_count)

    return mapann


def count_mapannotations(conn, mapann_ns=[], mapann_names=[],
                         mapann_value=None, mapann_query=None,
                         group_id=-1, experimenter_id=-1,
                         page=1, limit=settings.PAGE):
    ''' Count mapannotiation values

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param mapann_query The Map annotation value to filter by using like.
        @type mapann_query L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
    '''
    # map value is always one
    if mapann_value:
        return 1

    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=mapann_query, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()

    q = """
        select count( distinct mv.value) as childCount
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.wellSamples ws join ws.well w
             join w.plate p join p.screenLinks sl join sl.parent s
        where %s
        """ % (" and ".join(where_clause))

    counter = unwrap(qs.projection(q, params, service_opts))[0][0]

    q = """
        select count( distinct mv.value) as childCount
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.datasetLinks dsl
             join dsl.parent ds join ds.projectLinks pl join pl.parent p
        where %s
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    counter += unwrap(qs.projection(q, params, service_opts))[0][0]
    return counter


def marshal_mapannotations(conn, mapann_ns=[], mapann_names=[],
                           mapann_query=None, mapann_value=None,
                           group_id=-1, experimenter_id=-1,
                           page=1, limit=settings.PAGE):
    ''' Marshals mapannotation values

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param mapann_query The Map annotation value to filter by using like.
        @type mapann_query L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    mapannotations = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=mapann_query, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()

    # TODO: fix childCount
    if not mapann_value:
        q = """
            select
             mv.value as value,
             count(distinct i.id) as imgCount
            from ImageAnnotationLink ial
             join ial.child a
             join a.mapValue mv
             join ial.parent i
             left outer join i.wellSamples ws
             left outer join i.datasetLinks dil
            where %s AND
             (
                 (dil is null and ws is not null)
                 OR
                 (ws is null and dil is not null)
             )
            group by mv.value
            order by count(distinct i.id) DESC
            """ % (" and ".join(where_clause))
        _m = {}
        logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
        for e in qs.projection(q, params, service_opts):
            e = unwrap(e)
            _m[e[0]] = {'imgCount': e[1], 'childCount': None}

    else:
        _m = {mapann_value: {'imgCount': 0, 'childCount': 0}}

        q = """
            select count(distinct s.id) as childCount,
                   count(distinct i.id) as imgCount
            from ImageAnnotationLink ial join ial.child a join a.mapValue mv
                 join ial.parent i join i.wellSamples ws join ws.well w
                 join w.plate p join p.screenLinks sl join sl.parent s
            where %s
            """ % (" and ".join(where_clause))

        logger.debug("COUNT HQL QUERY: %s\nPARAMS: %r" % (q, params))
        for e in qs.projection(q, params, service_opts):
            e = unwrap(e)
            _m[mapann_value]['childCount'] += e[0]
            _m[mapann_value]['imgCount'] += e[1]

        q = """
            select count(distinct p.id) as childCount,
                   count(distinct i.id) as imgCount
            from ImageAnnotationLink ial join ial.child a join a.mapValue mv
                 join ial.parent i join i.datasetLinks dsl
                 join dsl.parent ds join ds.projectLinks pl join pl.parent p
            where %s
            """ % (" and ".join(where_clause))

        logger.debug("COUNT HQL QUERY: %s\nPARAMS: %r" % (q, params))
        for e in qs.projection(q, params, service_opts):
            e = unwrap(e)
            _m[mapann_value]['childCount'] += e[0]
            _m[mapann_value]['imgCount'] += e[1]

    for k, v in _m.iteritems():
        c = v["imgCount"]
        e = [k,
             "%s (%d)" % (k, v["imgCount"]),
             None,
             experimenter_id,  # e[0]["ownerId"],
             {},  # e[0]["map_details_permissions"],
             None,  # e[0]["ns"],
             v["childCount"]]
        mt = _marshal_map(conn, e[0:7])
        mt.update({'extra': {'counter': c}})
        mapannotations.append(mt)

    return mapannotations


def marshal_screens(conn, mapann_ns=[], mapann_names=[],
                    mapann_value=None, mapann_query=None,
                    group_id=-1, experimenter_id=-1,
                    page=1, limit=settings.PAGE):

    ''' Marshals screens

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param mapann_value The Map annotation value to filter by.
        @type mapann_value L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    screens = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=mapann_query, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()
    q = """
        select new map(screen.id as id,
               screen.name as name,
               screen.details.owner.id as ownerId,
               screen as screen_details_permissions,
               count(distinct p.id) as childCount,
               count(distinct i.id) as imgCount)
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.wellSamples ws join ws.well w
             join w.plate p join p.screenLinks sl join sl.parent screen
        where %s
        group by screen.id, screen.name
        order by lower(screen.name), screen.id
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)
        e = [e[0]["id"],
             "%s (%d)" % (e[0]["name"], e[0]["imgCount"]),
             e[0]["ownerId"],
             e[0]["screen_details_permissions"],
             e[0]["childCount"]]
        ms = _marshal_screen(conn, e[0:5])
        ms.update({'extra': {'value': mapann_value}})
        screens.append(ms)

    return screens


def marshal_projects(conn, mapann_ns=[], mapann_names=[],
                     mapann_value=None, mapann_query=None,
                     group_id=-1, experimenter_id=-1,
                     page=1, limit=settings.PAGE):

    ''' Marshals projects

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param mapann_value The Map annotation value to filter by.
        @type mapann_value L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    projects = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=mapann_query, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()
    q = """
        select new map(project.id as id,
               project.name as name,
               project.details.owner.id as ownerId,
               project as project_details_permissions,
               count(distinct dataset.id) as childCount,
               count(distinct i.id) as imgCount)
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.datasetLinks dil
             join dil.parent dataset join dataset.projectLinks pl
             join pl.parent project
        where %s
        group by project.id, project.name
        order by lower(project.name), project.id
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)
        e = [e[0]["id"],
             "%s (%d)" % (e[0]["name"], e[0]["imgCount"]),
             e[0]["ownerId"],
             e[0]["project_details_permissions"],
             e[0]["childCount"]]
        ms = _marshal_screen(conn, e[0:5])
        ms.update({'extra': {'value': mapann_value}})
        projects.append(ms)

    return projects


def marshal_datasets(conn, project_id,
                     mapann_value, mapann_ns=[], mapann_names=[],
                     group_id=-1, experimenter_id=-1,
                     page=1, limit=settings.PAGE):

    ''' Marshals plates

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param project_id The Project ID to filter by.
        @type project_id L{long}
        @param mapann_value The Map annotation value to filter by.
        @type mapann_value L{string}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    datasets = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=None, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    params.addLong("pid", project_id)
    where_clause.append('project.id = :pid')

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()
    q = """
        select new map(dataset.id as id,
               dataset.name as name,
               dataset.details.owner.id as ownerId,
               dataset as dataset_details_permissions,
               count(distinct i.id) as childCount)
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.datasetLinks dil
             join dil.parent dataset join dataset.projectLinks pl
             join pl.parent project
        where %s
        group by dataset.id, dataset.name
        order by lower(dataset.name), dataset.id
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)
        e = [e[0]["id"],
             e[0]["name"],
             e[0]["ownerId"],
             e[0]["dataset_details_permissions"],
             e[0]["childCount"]]
        mp = _marshal_plate(conn, e[0:5])
        mp.update({'extra': {'value': mapann_value, 'node': 'dataset'}})
        datasets.append(mp)

    return datasets


def marshal_plates(conn, screen_id,
                   mapann_value, mapann_ns=[], mapann_names=[],
                   group_id=-1, experimenter_id=-1,
                   page=1, limit=settings.PAGE):

    ''' Marshals plates

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param screen_id The Screen ID to filter by.
        @type screen_id L{long}
        @param mapann_value The Map annotation value to filter by.
        @type mapann_value L{string}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    plates = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=None, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    params.addLong("sid", screen_id)
    where_clause.append('screen.id = :sid')

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()
    q = """
        select new map(plate.id as id,
               plate.name as name,
               plate.details.owner.id as ownerId,
               plate as plate_details_permissions,
               count(distinct i.id) as childCount)
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
             join ial.parent i join i.wellSamples ws join ws.well w
             join w.plate plate join plate.screenLinks sl join
             sl.parent screen
        where %s
        group by plate.id, plate.name
        order by lower(plate.name), plate.id
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)
        e = [e[0]["id"],
             e[0]["name"],
             e[0]["ownerId"],
             e[0]["plate_details_permissions"],
             e[0]["childCount"]]
        mp = _marshal_plate(conn, e[0:5])
        mp.update({'extra': {'value': mapann_value, 'node': 'plate'}})
        plates.append(mp)

    return plates


def marshal_images(conn, parent, parent_id, mapann_value,
                   mapann_ns=[], mapann_names=[],
                   load_pixels=False,
                   group_id=-1, experimenter_id=-1,
                   page=1, date=False, thumb_version=False,
                   limit=settings.PAGE):

    ''' Marshals images

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param plate_id The Plate ID to filter by.
        @type plate_id L{long}
        @param mapann_value The Map annotation value to filter by.
        @type mapann_value L{string}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param load_pixels Whether to load the X,Y,Z dimensions
        @type load_pixels Boolean
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    images = []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=None, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    from_join_clauses = []

    qs = conn.getQueryService()

    extraValues = ""
    if load_pixels:
        extraValues = """
             ,
             pix.sizeX as sizeX,
             pix.sizeY as sizeY,
             pix.sizeZ as sizeZ
             """

    if date:
        extraValues += """,
            image.details.creationEvent.time as date,
            image.acquisitionDate as acqDate
            """

    q = """
        select new map(image.id as id,
               image.name as name,
               image.details.owner.id as ownerId,
               image as image_details_permissions,
               image.fileset.id as filesetId %s)
        from Image image
        """ % extraValues

    if load_pixels:
        # We use 'left outer join', since we still want images if no pixels
        q += ' left outer join image.pixels pix '

    q += """
        where image.id in (
        """

    if parent == 'plate':
        from_join_clauses.append("""
            ImageAnnotationLink ial
            join ial.child a
            join a.mapValue mv
            join ial.parent image
            join image.wellSamples ws join ws.well well
            join well.plate plate
        """)
        params.addLong("pid", parent_id)
        where_clause.append('plate.id = :pid')
    if parent == 'dataset':
        from_join_clauses.append("""
            ImageAnnotationLink ial
            join ial.child a
            join a.mapValue mv
            join ial.parent image
            join image.datasetLinks dil join dil.parent dataset
        """)
        params.addLong("did", parent_id)
        where_clause.append('dataset.id = :did')

    q += """
        %s %s
        order by lower(image.name))
        """ % (' select image.id from ' + ' '.join(from_join_clauses),
               build_clause(where_clause, 'where', 'and'))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)[0]
        d = [e["id"],
             e["name"],
             e["ownerId"],
             e["image_details_permissions"],
             e["filesetId"]]
        kwargs = {'conn': conn, 'row': d[0:5]}
        if load_pixels:
            d = [e["sizeX"], e["sizeY"], e["sizeZ"]]
            kwargs['row_pixels'] = d
        if date:
            kwargs['acqDate'] = e['acqDate']
            kwargs['date'] = e['date']

        images.append(_marshal_image(**kwargs))

    # Load thumbnails separately
    # We want version of most recent thumbnail (max thumbId) owned by user
    if thumb_version and len(images) > 0:
        userId = conn.getUserId()
        iids = [i['id'] for i in images]
        params = omero.sys.ParametersI()
        params.addIds(iids)
        params.add('thumbOwner', wrap(userId))
        q = """select image.id, thumbs.version from Image image
            join image.pixels pix join pix.thumbnails thumbs
            where image.id in (:ids)
            and thumbs.id = (
                select max(t.id)
                from Thumbnail t
                where t.pixels = pix.id
                and t.details.owner.id = :thumbOwner
            )
            """
        thumbVersions = {}
        logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
        for t in qs.projection(q, params, service_opts):
            iid, tv = unwrap(t)
            thumbVersions[iid] = tv
        # For all images, set thumb version if we have it...
        for i in images:
            if i['id'] in thumbVersions:
                i['thumbVersion'] = thumbVersions[i['id']]

    return images


def load_mapannotation(conn, mapann_ns=[], mapann_names=[], mapann_value=None,
                       group_id=-1, experimenter_id=-1,
                       page=1, limit=settings.PAGE):
    ''' Marshals mapannotation values

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation names to filter by.
        @type mapann_names L{string}
        @param mapann_query The Map annotation value to filter by using like.
        @type mapann_query L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''

    annotations = []
    experimenters = {}
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=None, mapann_value=mapann_value,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()

    q = """
        select distinct a
            from Annotation a
            join fetch a.details.creationEvent
            join fetch a.details.owner
            join a.mapValue mv where %s
            order by a.ns asc
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    for ann in qs.findAllByQuery(q, params, service_opts):
        d = _marshal_annotation(conn, ann, None)
        exp = _marshal_exp_obj(ann.details.owner)
        experimenters[exp['id']] = exp
        annotations.append(d)

    experimenters = experimenters.values()

    return annotations, experimenters


def marshal_autocomplete(conn, query=None,
                         mapann_ns=[], mapann_names=None,
                         group_id=-1, experimenter_id=-1,
                         page=1, limit=settings.PAGE):
    ''' Marshals mapannotation values for autocomplete

        @param conn OMERO gateway.
        @type conn L{omero.gateway.BlitzGateway}
        @param query The Map annotation value to filter by using like.
        @type query L{string}
        @param mapann_ns The Map annotation namespace to filter by.
        @type mapann_ns L{string}
        @param mapann_names The Map annotation name to filter by.
        @type mapann_names L{string}
        @param group_id The Group ID to filter by or -1 for all groups,
        defaults to -1
        @type group_id L{long}
        @param experimenter_id The Experimenter (user) ID to filter by
        or -1 for all experimenters
        @type experimenter_id L{long}
        @param page Page number of results to get. `None` or 0 for no paging
        defaults to 1
        @type page L{long}
        @param limit The limit of results per page to get
        defaults to the value set in settings.PAGE
        @type page L{long}
    '''
    if not query:
        return []
    params, where_clause = _set_parameters(
        mapann_ns=mapann_ns, mapann_names=mapann_names,
        mapann_query=query, mapann_value=None,
        params=None, experimenter_id=experimenter_id,
        page=page, limit=limit)

    service_opts = deepcopy(conn.SERVICE_OPTS)

    # Set the desired group context
    if group_id is None:
        group_id = -1
    service_opts.setOmeroGroup(group_id)

    qs = conn.getQueryService()

    q = """
        select new map(mv.value as value)
        from ImageAnnotationLink ial join ial.child a join a.mapValue mv
        where %s
        group by mv.value
        order by lower(mv.value)
        """ % (" and ".join(where_clause))

    logger.debug("HQL QUERY: %s\nPARAMS: %r" % (q, params))
    autocomplete = []
    for e in qs.projection(q, params, service_opts):
        e = unwrap(e)
        autocomplete.append({'value': e[0]["value"]})
    return autocomplete
