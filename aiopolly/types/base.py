import datetime
import functools
import logging
from typing import TYPE_CHECKING, Dict, Set, Optional, Callable, cast

from pydantic import BaseModel, Extra, Any
from pydantic.json import timedelta_isoformat
from pydantic.main import validate_model

from ..utils import json
from ..utils.case import to_camel

__all__ = ['BasePollyObject']

log = logging.getLogger('aiopolly')


class BasePollyObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow
        use_enum_values = True
        validate_assignment = True

        json_encoders = {
            datetime.datetime: lambda v: (v.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)).total_seconds(),
            datetime.timedelta: timedelta_isoformat,
        }

    # need to suppress unwanted validation exceptions
    # noinspection PyMissingConstructor
    def __init__(self, **data: Any) -> None:
        if TYPE_CHECKING:  # pragma: no cover
            self.__values__: Dict[str, Any] = {}
            self.__fields_set__: Set[str] = set()
        values, fields_set, error = validate_model(self, data, raise_exc=False)
        object.__setattr__(self, '__values__', values)
        object.__setattr__(self, '__fields_set__', fields_set)

        if error:
            try:
                trust_api_responses = self.polly._trust_api_responses
            except RuntimeError:
                trust_api_responses = True

            if trust_api_responses:
                log.exception('Got unexpected params in API response:', exc_info=error)
            else:
                raise error

    def dict(self, *,
             include: Set[str] = None,
             exclude: Set[str] = None,
             by_alias: bool = False,
             skip_defaults: bool = False,
             use_camel: bool = False,
             ) -> dict:

        result = BaseModel.dict(self, include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults)

        if use_camel:
            return to_camel(result)
        return result

    def json(self, *,
             include: Set[str] = None,
             exclude: Set[str] = None,
             by_alias: bool = False,
             skip_defaults: bool = False,
             encoder: Optional[Callable[[Any], Any]] = None,
             use_camel: bool = False,
             **dumps_kwargs: Any,
             ) -> str:

        encoder = cast(Callable[[Any], Any], encoder or self._json_encoder)
        return json.dumps(
            self.dict(use_camel=use_camel, include=include,
                      exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults),
            default=encoder,
            **dumps_kwargs
        )

    @property
    @functools.lru_cache()
    def polly(self):
        """
        :rtype: aiopolly.polly.Polly
        """
        from .. import Polly
        polly = Polly.get_current()
        if polly is None:
            raise RuntimeError("Can't get polly instance from context. "
                               "You can fix it with setting current instance: "
                               "'Polly.set_current(polly_instance)'")
        return polly

    def __hash__(self):
        def _hash(obj):
            buf = 0
            if isinstance(obj, list):
                for item in obj:
                    buf += _hash(item)
            elif isinstance(obj, dict):
                for dict_key, dict_value in obj.items():
                    buf += hash(dict_key) + _hash(dict_value)
            else:
                try:
                    buf += hash(obj)
                except TypeError:  # Skip unhashable objects
                    pass
            return buf

        result = 0
        for key, value in sorted(self.fields.items()):
            result += hash(key) + _hash(value)

        return result
