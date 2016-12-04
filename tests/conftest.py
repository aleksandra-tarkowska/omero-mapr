import os
import django

from django.conf import settings

# We manually designate which settings we will be using in an environment
# variable. This is similar to what occurs in the `manage.py`
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omeroweb.settings')


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = False
    settings.MAPR_CONFIG_AS_DICT = {
        "gene": {
            "default": ["Gene Symbol"],
            "all": ["Gene Symbol", "Gene Identifier"],
            "ns": ["openmicroscopy.org/omero/bulk_annotations"],
            "label": "Gene"
        },
    }
    django.setup()
