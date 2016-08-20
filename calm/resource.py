from untt import Entity
from untt.util import entity_base
from untt.types import (Integer, Number, String,  # noqa
                        Boolean, Array, Datetime)


@entity_base
class Resource(Entity):
    schema_root = True

    def __json__(self):
        """Proxies `Entity.to_json()`."""
        return self.to_json()  # pragma: no cover
