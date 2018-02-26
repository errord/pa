#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


from datetime import datetime
import hashlib


def to_utf8(text):
    if isinstance(text, unicode):
        return text.encode("utf8")
    if isinstance(text, datetime):
        return text.strftime("%Y-%m-%d %H:%M:%S")
    return str(text)

def md5(text):
    return hashlib.md5(text).hexdigest()

