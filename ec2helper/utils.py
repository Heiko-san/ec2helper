# -*- coding: utf-8 -*-
"""
Common utils.
"""
from __future__ import unicode_literals, absolute_import
import six
import re
import json
from datetime import datetime, date


INTEGER = re.compile(r"^-?\d+$")                                                
FLOAT = re.compile(r"^-?\d+(\.\d+)?$")


def json_dump(data):
    """
    Convenience helper for human readable JSON data with datetime support.
    """
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return "{0} ({1})".format(obj.isoformat(), type(obj))
        else:
            return "{0} ({1})".format(str(obj), type(obj))
    print(json.dumps(
        data,
        indent=4,
        sort_keys=True,
        default=json_serial
    ))


def parse_value(value):
    if value == "": return None
    return value


def tags_to_dict(tags):
    """
    Convert AWS style tags to dict.
    """
    return dict([(x["Key"], x["Value"]) for x in tags])


def dict_to_tags(tags):
    """
    Convert dict to AWS style tags.
    """
    return [{"Key": k, "Value": v} for k, v in six.iteritems(tags)]
