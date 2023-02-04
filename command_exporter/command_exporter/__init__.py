import json
import os.path
from enum import Enum
from pathlib import Path
from typing import Callable

from mcdreforged.command.builder.nodes.arguments import Number, Integer, Float, Text, QuotableText, GreedyText, Boolean, \
    Enumeration
from mcdreforged.command.builder.nodes.basic import Literal, AbstractNode
from mcdreforged.mcdr_server import MCDReforgedServer
from mcdreforged.plugin.plugin_registry import PluginCommandHolder
from mcdreforged.plugin.server_interface import PluginServerInterface

from .config import Config

mcdr_server: MCDReforgedServer
config: Config
old_on_plugin_registry_changed: Callable

class NodeTypes(Enum):
    LITERAL = Literal
    NUMBER = Number
    INTEGER = Integer
    FLOAT = Float
    TEXT = Text
    QUOTABLE_TEXT = QuotableText
    GREEDY_TEXT = GreedyText
    BOOLEAN = Boolean
    ENUMERATION = Enumeration

class Node:
    def __init__(self, name: str, node: AbstractNode):
        self.name = name
        self.type = None
        self.children = []

        # get type
        try:
            self.type = NodeTypes(node.__class__)
        except ValueError:
            self.type = NodeTypes.TEXT

        # Literal children
        for literal, literal_children in node._children_literal.items():
            self.children.append(Node(literal, literal_children[0]))

        # Argument children
        for argument_child in node._children:
            self.children.append(
                Node(
                    argument_child._ArgumentNode__name,
                    argument_child
                )
            )

    @property
    def dict(self):
        return {
            'name': self.name,
            'type': self.type.name,
            'children': [i.dict for i in self.children]
        }

def get_node_json(path: str):
    path = Path(path)
    if not os.path.exists(path.parent):
        os.makedirs(path.parent)
    root_nodes = mcdr_server.command_manager.root_nodes
    json_data = {'data': []}
    for key, value in root_nodes.items():
        plugin_command_holder: PluginCommandHolder = value[0]
        json_data['data'].append(Node(key, plugin_command_holder.node).dict)
    print(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4)

def on_load(server: PluginServerInterface, prev_module):
    global mcdr_server
    global config
    mcdr_server = server._mcdr_server
    config = server.load_config_simple(file_name="config/command_exporter.json", in_data_folder=False, target_class=Config)

    get_node_json(config.node_path)

    # Call register when register command
    global old_on_plugin_registry_changed
    old_on_plugin_registry_changed = mcdr_server.on_plugin_registry_changed

    def new_on_plugin_registry_changed():
        server.logger.debug('on_plugin_registry_changed')
        old_on_plugin_registry_changed()
        get_node_json(config.node_path)

    mcdr_server.on_plugin_registry_changed = new_on_plugin_registry_changed

def on_unload(server: PluginServerInterface):
    mcdr_server.on_plugin_registry_changed = old_on_plugin_registry_changed