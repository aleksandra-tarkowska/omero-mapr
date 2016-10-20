//   Copyright (C) 2016 University of Dundee & Open Microscopy Environment.
//   All rights reserved.

//   This program is free software: you can redistribute it and/or modify
//   it under the terms of the GNU Affero General Public License as
//   published by the Free Software Foundation, either version 3 of the
//   License, or (at your option) any later version.

//   This program is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU Affero General Public License for more details.

//   You should have received a copy of the GNU Affero General Public License
//   along with this program.  If not, see <http://www.gnu.org/licenses/>.

//   Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>,

//   Version: 1.0

//   Here we override jstree setup and configure


// jQuery load callback...

$(function () {

    var jstree = $.jstree.reference('#dataTree');

    // payload
    var oldData = jstree.settings.core.data;
    jstree.settings.core.data = function(node, callback, payload) {
        if (payload === undefined) {
            payload = {};
        }
        if (MAPANNOTATIONS.CTX.value.length > 0) {
            payload['value'] = MAPANNOTATIONS.CTX.value;
        }
        if (MAPANNOTATIONS.CTX.query.length > 0) {
            payload['query'] = MAPANNOTATIONS.CTX.query;
        }
        oldData.apply(jstree, [node, callback, payload]);
    }

    // custom type map
    jstree.settings.types['#'].valid_children = ['map'];
    jstree.settings.types['map'] = {
        'icon': WEBCLIENT.URLS.static_webclient + 'image/left_sidebar_icon_tag.png',
        'valid_children': ['project', 'screen'],
        'draggable': false
    }

    if (MAPANNOTATIONS.CTX.label.length > 0) {
        jstree.settings.types['map'].icon = MAPANNOTATIONS.URLS.static_webclient + 'image/' + MAPANNOTATIONS.CTX.label + '_icon_16x16.png';
    }
    jstree.settings.types['plate'].valid_children = ['image'];

    jstree.settings.sort = function(nodeId1, nodeId2) {
        var inst = this;
        var node1 = inst.get_node(nodeId1);
        var node2 = inst.get_node(nodeId2);

        function sortingStrategy(n1, n2) {
            // sorting strategy
            // sort by extra.imgCount or by name

            if(n1.type === 'experimenter') {
                if (n1.data.obj.id === WEBCLIENT.USER.id) {
                    return -1;
                } else if (n2.data.obj.id === WEBCLIENT.USER.id) {
                    return 1;
                }
            }

            var s1 = null;
            var s2 = null;
            var revert = false;
            // extra:counter shoudl take priority in sorting
            if (n1.data.obj.extra && n1.data.obj.extra.counter) {
                s1 = parseInt(n1.data.obj.extra.counter);
                s2 = parseInt(n2.data.obj.extra.counter);
                revert = true
            }
            // If counters are the same sort by Name
            if (s1 === s2) {
                // otherwise sort by name
                s1 = n1.text.toLowerCase();
                s2 = n2.text.toLowerCase();
            }
            // If names are same, sort by ID
            if (s1 === s2) {
                return n1.data.obj.id <= n2.data.obj.id ? -1 : 1;
            }
            if (revert)
                return s1 <= s2 ? 1 : -1;
            return s1 <= s2 ? -1 : 1;
        }

        return sortingStrategy(node1, node2);
    };

});
