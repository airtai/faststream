from typing import TYPE_CHECKING, Dict, Optional

from nats.js.api import ObjectStoreConfig

if TYPE_CHECKING:
    from nats.js import JetStreamContext
    from nats.js.api import Placement, StorageType
    from nats.js.object_store import ObjectStore


class OSBucketDeclarer:
    buckets: Dict[str, "ObjectStore"]

    def __init__(self, connection: "JetStreamContext") -> None:
        self._connection = connection
        self.buckets = {}

    async def create_object_store(
        self,
        bucket: str,
        *,
        description: Optional[str] = None,
        ttl: Optional[float] = None,
        max_bytes: Optional[int] = None,
        storage: Optional["StorageType"] = None,
        replicas: int = 1,
        placement: Optional["Placement"] = None,
        # custom
        declare: bool = True,
    ) -> "ObjectStore":
        if (object_store := self.buckets.get(bucket)) is None:
            if declare:
                object_store = await self._connection.create_object_store(
                    bucket=bucket,
                    config=ObjectStoreConfig(
                        bucket=bucket,
                        description=description,
                        ttl=ttl,
                        max_bytes=max_bytes,
                        storage=storage,
                        replicas=replicas,
                        placement=placement,
                    ),
                )
            else:
                object_store = await self._connection.object_store(bucket)

            self.buckets[bucket] = object_store

        return object_store
