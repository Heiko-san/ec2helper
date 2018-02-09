# -*- coding: utf-8 -*-
"""
Common utils.
"""
from __future__ import unicode_literals, absolute_import
import six
import re
import json
import requests
from ec2_metadata import ec2_metadata
from datetime import datetime, date
from dateutil import parser


INTEGER = re.compile(r"^-?\d+$")
FLOAT = re.compile(r"^-?\d+(\.\d+)?$")
BOOLTRUE = re.compile(r"^true$", flags=re.IGNORECASE)
BOOLFALSE = re.compile(r"^false$", flags=re.IGNORECASE)


try:
    # This request still succeeded with a timeout of 0.001, so 0.5 should be a
    # good compromise between stability and load time on none EC2 instances.
    requests.get("http://169.254.169.254/latest/meta-data/reservation-id",
        timeout=0.5)
except requests.exceptions.ConnectTimeout:
    IS_EC2 = False
else:
    #: This variable indicates if calling the EC2 metadata API succeeded, thus
    #: if we're on an EC2 instance.
    IS_EC2 = True


def metadata(attribute):
    """
    Get metadata attribute if on EC2, None otherwise.
    """
    if IS_EC2:
        return getattr(ec2_metadata, attribute)
    return None


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


def _parse_value(value):
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


def _string_value(value):
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
    return dict([(x["Key"], _parse_value(x["Value"])) for x in tags])


def dict_to_tags(tags):
    """
    Convert dict to AWS style tags.
    """
    return [{"Key": k, "Value": _string_value(v)} for k, v in
        six.iteritems(tags)]
