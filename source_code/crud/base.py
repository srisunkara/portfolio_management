# source_code/crud/base.py
from __future__ import annotations

from threading import RLock
from typing import Generic, TypeVar, Dict, List, Optional, Any, Type

from pydantic import BaseModel

from source_code.config import pg_db_conn_manager

ModelT = TypeVar("ModelT", bound=BaseModel)


class InMemoryDB(Generic[ModelT]):
    """
    Thread-safe, very simple in-memory 'DB' for demo/testing.
    Stores objects by their primary key (field ending with '_id').
    """
    def __init__(self, model_cls: Type[ModelT], pk_field: Optional[str] = None):
        self._model_cls = model_cls
        self._pk_field = pk_field or self._detect_pk_field(model_cls)
        self._items: Dict[Any, ModelT] = {}
        self._lock = RLock()

    @staticmethod
    def _detect_pk_field(model_cls: Type[BaseModel]) -> str:
        # Pick the first field that ends with '_id' otherwise first field
        for name in model_cls.model_fields.keys():
            if name.endswith("_id"):
                return name
        # Fallback to the first declared field
        return next(iter(model_cls.model_fields.keys()))

    @property
    def pk_field(self) -> str:
        return self._pk_field

    def save(self, item: ModelT) -> ModelT:
        pk = getattr(item, self._pk_field)
        with self._lock:
            self._items[pk] = item
        return item

    def get(self, pk: Any) -> Optional[ModelT]:
        with self._lock:
            return self._items.get(pk)

    def update(self, pk: Any, item: ModelT) -> ModelT:
        with self._lock:
            if pk not in self._items:
                raise KeyError(f"{self._model_cls.__name__} with {self._pk_field}={pk} not found")
            self._items[pk] = item
            return item

    def delete(self, pk: Any) -> bool:
        with self._lock:
            return self._items.pop(pk, None) is not None

    def list_all(self) -> List[ModelT]:
        with self._lock:
            return list(self._items.values())


class BaseCRUD(Generic[ModelT]):
    """
    Reusable CRUD layer on top of an InMemoryDB.
    """
    def __init__(self, model_cls: Type[ModelT]):
        self.model_cls = model_cls
        self.db = InMemoryDB[ModelT](model_cls)

    @property
    def pk_field(self) -> str:
        return self.db.pk_field

    def save(self, item: ModelT) -> ModelT:
        return self.db.save(item)

    def get_security(self, pk: Any) -> Optional[ModelT]:
        return self.db.get(pk)

    def update(self, pk: Any, item: ModelT) -> ModelT:
        # Ensure path pk matches the object pk
        item_pk = getattr(item, self.pk_field)
        if item_pk != pk:
            raise ValueError(f"Path {self.pk_field}={pk} does not match body {self.pk_field}={item_pk}")
        return self.db.update(pk, item)

    def delete(self, pk: Any) -> bool:
        return self.db.delete(pk)

    def list_all(self) -> List[ModelT]:
        return self.db.list_all()
