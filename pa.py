# -*- coding: utf-8 -*-
#
# Copyright 2015 error.d
# by error.d@gmail.com
# 2015-04-23
#

"""
PA -- Product Assembly
"""

import logging
import inspect
import threading

from leobase.pa.pa_plugin import PaPlugin
from leobase.pa.pa_resource import PaResource

PLUGIN_PREFIX = "pa_plugin__"
PLUGIN_POSTFIX = ".py"

"""
config file format:
{
  'plugin_path' : '',
  'PluginName' : {
                  xx
                  }
}
"""


class ProductAssembly(object):
    """
    Product Assembly
    """

    cfg = None
    is_initialize = False
    initialize_lock = threading.Lock()
    
    plugin_map = dict()
    action_plugin_map = dict()

    action_list = [
        "nop",
        "detail",
        "price_calendar"]

    @classmethod
    def get_action_list(cls):
        """获取接口列表"""
        return cls.action_list

    @classmethod
    def register_plugin(cls, plugin):
        """注册插件"""
        plugin_name = plugin.plugin_name()
        cls.plugin_map[plugin_name] = plugin

    @classmethod
    def register_action(cls, plugin):
        def _add_action(action):
            if action not in cls.action_plugin_map:
                cls.action_plugin_map[action] = []
            cls.action_plugin_map[action].append(plugin)

        actions = cls.get_action_list()
        for action in actions:
            if plugin.match_action(action):
                _add_action(action)

    @classmethod
    def _import_plugin_path(cls, plugin_path):
        import os
        import os.path
        import sys

        plugins_class = []
        def _get_plugins(module):
            symbol_list = dir(module)
            for symbol in symbol_list:
                obj = module.__dict__[symbol]
                if inspect.getmodule(obj) == module and \
                       inspect.isclass(obj) and \
                       issubclass(obj, PaPlugin):
                    plugins_class.append(obj)

        sys.path.insert(0, plugin_path)
        for parent, _, filenames in os.walk(plugin_path):
            for filename in filenames:
                if filename.startswith(PLUGIN_PREFIX) and \
                       filename.endswith(PLUGIN_POSTFIX):
                    plugin_path = os.path.join(parent,filename)
                    module_name = filename[:-3]
                    logging.debug('load plugin module:%s file: %s',
                                  module_name, plugin_path)
                    plugin_module = __import__(module_name)
                    _get_plugins(plugin_module)
        sys.path.pop(0)
        return plugins_class

    @classmethod
    def _load_plugin_class_from_palib(cls):
        import leobase.pa.plugin
        palib_plugin_path = leobase.pa.plugin.__path__[0]
        return cls._import_plugin_path(palib_plugin_path)

    @classmethod
    def _load_plugin_class_from_cfg(cls):
        plugin_path = cls.cfg.get('plugin_path', None) if cls.cfg else None
        return cls._import_plugin_path(plugin_path) if plugin_path else []

    @classmethod
    def load_plugin(cls):
        """初始化插件"""

        plugin_class = cls._load_plugin_class_from_palib()
        plugin_class += cls._load_plugin_class_from_cfg()

        for pc in plugin_class:
            logging.debug('load plugin class:%s', pc)
            plugin = pc()
            plugin_cfg = cls.cfg.get(plugin.plugin_name(), None) if cls.cfg else None
            par = PaResource.instance()
            plugin.set_pa_cfg(cls.cfg)
            plugin.set_plugin_cfg(plugin_cfg)
            plugin.set_pa_resource(par)
            if plugin.initialize(cls, cls.cfg, plugin_cfg, par) is False:
                return

            # register plugin
            ProductAssembly.register_plugin(plugin)
            ProductAssembly.register_action(plugin)

    @classmethod
    def unload_plugin(cls, plugin_name):
        def _remove_on_action_map():
            pmap = cls.action_plugin_map
            for action, plugin_list in pmap.items():
                pmap[action] = [plugin for plugin in plugin_list \
                                if plugin.plugin_name() != plugin_name]

        _remove_on_action_map()
        del cls.plugin_map[plugin_name]

    @classmethod
    def has_plugin(cls, plugin_name):
        return bool(cls.plugin_map.get(plugin_name, False))


    @classmethod
    def plugin_has_action(cls, plugin_name, action):
        plugin = cls.plugin_map.get(plugin_name, None)
        if not plugin:
            return False
        return bool(plugin.match_action(action))

    @classmethod
    def dump_plugin(cls):
        """输出一下当前进程中的插件集合信息"""
        for plugin_name, plugin in cls.plugin_map.items():
            logging.info('plugin name:%s object:%s', plugin_name, plugin)

    @classmethod
    def global_initialize(cls, cfg, resource_dict=None):
        cls.cfg = cfg
        if cls.is_initialize is True:
            return

        if resource_dict:
            pa_resource = PaResource.instance()
            for resource_name, resource in resource_dict.items():
                pa_resource.add_resource(resource_name, resource)
        
        cls.initialize_lock.acquire()
        if cls.is_initialize is False:
            cls.is_initialize = True
            ProductAssembly.load_plugin()
        cls.initialize_lock.release()

    def __init__(self, plugin_pipeline):
        self._plugin_pipeline = plugin_pipeline

    def _match_plugins_from_action(self, action, product):
        plugins = []
        action_plugins = self.action_plugin_map.get(action, [])
        for plugin in action_plugins:
            if plugin.match(product):
                logging.debug('match success plugin name: %s', plugin.plugin_name())
                plugins.append(plugin)
        return plugins

    def _run_plugins(self, action, plugins, product, **kwargs):
        for plugin in plugins:
            plugin.assembly(action, product, **kwargs)

    ### Short Interface

    def __getattr__(self, action_name):
        return lambda product, **kwargs: self.assembly(action_name, product, **kwargs)

    ### User Interface

    @staticmethod
    def add_resource(resource_name, resource):
        PaResource.instance().add_resource(resource_name, resource)

    def assembly(self, action, product, **kwargs):
        if action not in self.get_action_list():
            logging.error('Unknow action: %s' % action)
            return None
        
        plugins = self._match_plugins_from_action(action, product)
        self._run_plugins(action, plugins, product, **kwargs)
        return product
