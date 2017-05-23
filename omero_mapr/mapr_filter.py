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
import re

logger = logging.getLogger(__name__)


class MapFilter(object):

    # List of prefixes that are at the top level of the tree
    TOP_LEVEL_PREFIXES = ('project', 'screen',)

    # List of supported object types
    SUPPORTED_OBJECT_TYPES = (
        'project', 'screen',
    )

    PATH_REGEX = re.compile(
        r'(?P<object_type>\w+)\.?(?P<key>\w+)?[-=](?P<value>[^\|]*)\|?'
    )

    def __init__(self, mfilter):
        self._initially_select = list()
        if mfilter:
            for f in mfilter.split('|'):
                self._add_if_supported(f)

    def _add_if_supported(self, f):
        m = self.PATH_REGEX.match(f)
        if m is None:
            return
        object_type = m.group('object_type')
        key = m.group('key')
        value = m.group('value')
        if key is None:
            key = 'id'
        if object_type in self.SUPPORTED_OBJECT_TYPES:
            f = {
                'object': object_type,
                'key': key,
                'value': long(value) if key == 'id' else str(value),
            }
            self._initially_select.append(f)
