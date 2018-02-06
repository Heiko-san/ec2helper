# -*- coding: utf-8 -*-
"""
Common utils.
"""
from __future__ import unicode_literals, absolute_import
import six
import re
import json
from datetime import datetime, date
from dateutil import parser


INTEGER = re.compile(r"^-?\d+$")                                                
FLOAT = re.compile(r"^-?\d+(\.\d+)?$")
BOOLTRUE = re.compile(r"^true$", flags=re.IGNORECASE)
BOOLFALSE = re.compile(r"^false$", flags=re.IGNORECASE)


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
    """
    Convert string tag value to data types.
    """
    if value == "": return None
    if INTEGER.match(value): return int(value)
    if FLOAT.match(value): return float(value)
    if BOOLTRUE.match(value): return True
    if BOOLFALSE.match(value): return False
    try:
        value = parser.parse(value)
    except:
        pass
    return value


def string_value(value):
    """
    Convert data types to string tag value.
    """
    if value is None: return ""
    if isinstance(value, datetime): return value.isoformat()
    return six.text_type(value)


def tags_to_dict(tags):
    """
    Convert AWS style tags to dict.
    """
    return dict([(x["Key"], parse_value(x["Value"])) for x in tags])


def dict_to_tags(tags):
    """
    Convert dict to AWS style tags.
    """
    return [{"Key": k, "Value": string_value(v)} for k, v in six.iteritems(tags)]
