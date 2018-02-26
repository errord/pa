# -*- coding: utf-8 -*-
# Copyright 2015 error.d
# by error.d@gmail.com
# 2015-04-23
#

"""
Product Assembly Resource Manager
"""

import threading

class PaResource(object):

    par_instance = None
    instance_lock = threading.Lock()    
    
    @classmethod
    def instance(cls):
        if cls.par_instance is None:
            cls.instance_lock.acquire()
            if cls.par_instance is None:
                cls.par_instance = PaResource()
            cls.instance_lock.release()
        return cls.par_instance

    def __init__(self):
        self._resource = dict()

    def add_resource(self, resource_name, resource):
        self._resource[resource_name] = resource

    def get_resource(self, resource_name, default_resource=None):
        return self._resource.get(resource_name, default_resource)
