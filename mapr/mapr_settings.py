import django
from django.conf import settings
from omeroweb.settings import process_custom_settings, report_settings
import sys
import os
import json


def config_list_to_dict(config_list):
    config_dict = dict()
    for i in config_list:
        k = i.get('menu', None)
        if k is not None:
            if i.get('config', None) is not None:
                config_dict[k] = i['config']
    return config_dict


if django.VERSION < (1, 8):
    raise RuntimeError('MAPR requires Django 1.8+')


default_config = [
    {
        "menu": "gene",
        "config": {
            "default": ["Gene Symbol"],
            "all": ["Gene Symbol", "Gene Identifier"],
            "ns": ["openmicroscopy.org/mapr/gene"],
            "label": ["Gene"]
        }
    },
    {
        "menu": "genesupplementary",
        "config": {
            "default": [],
            "all": [],
            "ns": [
                "openmicroscopy.org/mapr/gene/supplementary"
            ],
            "label": ["Gene supplementary"]
        }
    },
    {
        "menu": "sirna",
        "config": {
            "default": ["siRNA Identifier"],
            "all": ["siRNA Identifier", "siRNA Pool Identifier"],
            "ns": ["openmicroscopy.org/mapr/sirna"],
            "label": ["siRNA"]
        }
    },
    {
        "menu": "sirnasupplementary",
        "config": {
            "default": [],
            "all": [],
            "ns": [
                "openmicroscopy.org/mapr/sirna/supplementary"
            ],
            "label": ["siRNA supplementary"]
        }
    },

    {
        "menu": "phenotype",
        "config": {
            "default": ["Phenotype"],
            "all": ["Phenotype", "Phenotype Term Accession"],
            "ns": ["openmicroscopy.org/mapr/phenotype"],
            "label": ["Phenotype"]
        }
    },
    {
        "menu": "compound",
        "config": {
            "default": ["Compound Name"],
            "all": ["Compound Name"],
            "ns": ["openmicroscopy.org/mapr/compound"],
            "label": ["Compound"]
        }
    },
    {
        "menu": "compoundsupplementary",
        "config": {
            "default": [],
            "all": [],
            "ns": ["openmicroscopy.org/mapr/compound/supplementary"],
            "label": ["Compound supplementary"]
        }
    },
    {
        "menu": "organism",
        "config": {
            "default": ["Organism"],
            "all": ["Organism"],
            "ns": ["openmicroscopy.org/mapr/organism"],
            "label": ["Organism"]
        }
    },
    {
        "menu": "others",
        "config": {
            "default": ["Others"],
            "all": ["Others"],
            "ns": ["openmicroscopy.org/omero/bulk_annotations"],
            "label": ["Others"]
        }
    }
]

# load settings
MAPR_SETTINGS_MAPPING = {
    "omeroweb.mapr.config":
        ["MAPR_CONFIG", json.dumps(default_config), json.loads, None],
    "omeroweb.mapr.favicon_webservice":
        ["FAVICON_WEBSERVICE",
            "http://www.google.com/s2/favicons?domain=", str, None]
    }

process_custom_settings(sys.modules[__name__], 'MAPR_SETTINGS_MAPPING')
report_settings(sys.modules[__name__])


MAPR_CONFIG_AS_DICT = config_list_to_dict(MAPR_CONFIG)  # noqa

DEFAULT_FAVICON = os.path.join(
    os.path.dirname(__file__), 'static', 'mapr', 'image',
    'favicon.png').replace('\\', '/')


class MaprSettings(object):

    MENU_MAPR = getattr(
        settings, 'MAPR_CONFIG_AS_DICT', MAPR_CONFIG_AS_DICT)
    DEFAULT_FAVICON = getattr(
        settings, 'DEFAULT_FAVICON', DEFAULT_FAVICON)
    FAVICON_WEBSERVICE = getattr(
        settings, 'FAVICON_WEBSERVICE', FAVICON_WEBSERVICE)  # noqa

mapr_settings = MaprSettings()
