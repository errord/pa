# -*- coding: utf-8 -*-
# Copyright 2015 error.d
# by error.d@gmail.com
# 2015-04-23
#

"""
PAPlugin -- Product Assembly Plugin PA插件的基类
"""

import logging

class PaPlugin(object):
    """
    Product Assembly
    """

    def __init__(self):
        self._cfg = None
        self._pa_resource = None

    def _action_handler_name(self, action):
        """
        return action handler name
        """

        return '%s_handler' % action

    def _action_handler(self, action, default_handler=None):
        """
        return action handler
        """

        return getattr(self, self._action_handler_name(action),
                       default_handler)

    def plugin_name(self):
        """
        return plugin name
        """

        return self._plugin_name

    def set_pa_cfg(self, pa_cfg):
        """
        set pa cfg
        """
        self._pa_cfg = pa_cfg

    def pa_cfg(self):
        """
        get pa config
        """

        return self._pa_cfg

    def set_plugin_cfg(self, plugin_cfg):
        """
        set plugin cfg
        """
        self._plugin_cfg= plugin_cfg

    def plugin_cfg(self):
        """
        get plugin config
        """

        return self._plugin_cfg

    def set_pa_resource(self, pa_resource):
        self._pa_resource = pa_resource

    def pa_resource(self):
        return self._pa_resource

    def match_action(self, action):
        """
        match action
        return True if support action else False
        """

        return hasattr(self, self._action_handler_name(action))

    def assembly(self, action, product, **kwargs):
        """
        action: action string

        dataset: the data exchange between plugins and plugins
        """

        action_handler = self._action_handler(action, None)
        if action_handler:
            dataset = dict()            
            action_handler(product, dataset, **kwargs)
            dataset = None

    # log method

    def _mk_msg(self, msg):
        return "[%s]: %s" % (self.plugin_name(), msg)

    def error(self, msg, *args):
        logging.error(self._mk_msg(msg), *args)

    def info(self, msg, *args):
        logging.info(self._mk_msg(msg), *args)

    def warn(self, msg, *args):
        logging.warn(self._mk_msg(msg), *args)

    def debug(self, msg, *args):
        logging.debug(self._mk_msg(msg), *args)


    #### subclass impletent method

    def initialize(self, pa, pa_cfg, plugin_cfg, pa_resource):
        """
        initialize plugin
        pa_cfg: pa global config
        plugin_cfg: plugin config
        pa_resource: pa resource
        """
        pass

    def match(self, product):
        """
        match product
        return True if support product else False
        """

        raise NotImplementedError, 'need impletent match method'

    ## impletent detail_handler(self, product, dataset, **kwargs) method
    ## impletent price_calendar_handler(self, product, dataset, **kwargs) method
