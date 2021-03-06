"""Using json from aiogram see: https://github.com/aiogram/aiogram/blob/dev-2.x/aiogram/utils/json.py"""

import importlib
import os

JSON = 'json'
RAPIDJSON = 'rapidjson'
UJSON = 'ujson'

# Detect mode
mode = JSON
for json_lib in (RAPIDJSON, UJSON):
    if 'DISABLE_' + json_lib.upper() in os.environ:
        continue

    try:
        json = importlib.import_module(json_lib)
    except ImportError:
        continue
    else:
        mode = json_lib
        break
if mode == RAPIDJSON:
    def dumps(data, ensure_ascii=False, number_mode=json.NM_NATIVE,
              datetime_mode=json.DM_ISO8601 | json.DM_NAIVE_IS_UTC, **kwargs):
        return json.dumps(data, ensure_ascii=ensure_ascii, number_mode=number_mode,
                          datetime_mode=datetime_mode, **kwargs)


    def loads(data):
        return json.loads(data, number_mode=json.NM_NATIVE,
                          datetime_mode=json.DM_ISO8601 | json.DM_NAIVE_IS_UTC)

elif mode == UJSON:
    def loads(data):
        return json.loads(data)


    def dumps(data, ensure_ascii=False, **kwargs):
        return json.dumps(data, ensure_ascii=ensure_ascii, **kwargs)

else:
    import json


    def dumps(data, ensure_ascii=False, **kwargs):
        return json.dumps(data, ensure_ascii=ensure_ascii, **kwargs)


    def loads(data, **kwargs):
        return json.loads(data, **kwargs)
