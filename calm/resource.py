from untt import Entity
from untt.util import entity_base


@entity_base
class Resource(Entity):
    schema_root = True

    def __json__(self):
        """Proxies `Entity.to_json()`."""
        return self.to_json()
