from mcdreforged.utils.serializer import Serializable


class Config(Serializable):
    node_path: str = 'server/config/node.json'