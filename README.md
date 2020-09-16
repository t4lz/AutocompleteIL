# AutocompleteIL
### A web API for parsing (partial) user address input, and getting auto-complete suggestions.
Could be used for creating custom address search bars that give suggestions as the user is typing, and send to the application a standard cannonized address or address code.

To try a simple example, run the server (run the `_index.py` file with python), then run the following python code (for example in an interactive interpreter like ipython)
```
import requests
import json

data = json.load({"text": "המלך ג'ורג' 77"})
headers = {'Content-Type': 'application/json'}
r = requests.post(data=data,url="http://0.0.0.0:5000/api/suggestions", headers=headers)
print(r.json())
```

## The JSON
The request query is sent to the server as an https POST with a json.
The `'text'` field is mandatory and containd the input to be parsed.
Optional fields include:

`'max'`: Maximal number of suggestions to return. It is recommended to use this field and limit the number of returned suggestions.
`'request_id'`: The client can include this field with an ID that will then also be included in the response. (This is useful in order know the order of requests and for example, avoid overwriting suggestions with suggestions for an earlier query, in case the order of the responses changes on their way through the internet.)

## The Data
The up-to-date **streets** data can be downloaded from here:

https://data.gov.il/dataset/israel-streets-synom/resource/bf185c7f-1a4e-4662-88c5-fa118a244bda

This is a direct link to the file:

https://data.gov.il/dataset/785ad9fb-6da6-426d-b5ea-b8e36febbc8a/resource/bf185c7f-1a4e-4662-88c5-fa118a244bda/download/bf185c7f-1a4e-4662-88c5-fa118a244bda.csv



The up-to-date **cities population** data can be downloaded from here:

https://data.gov.il/dataset/residents_in_israel_by_communities_and_age_groups/resource/64edd0ee-3d5d-43ce-8562-c336c24dbc1f

This is a direct link to the file:

https://data.gov.il/dataset/00172ee8-4433-4d5d-8fd4-11f0f08ce5c4/resource/64edd0ee-3d5d-43ce-8562-c336c24dbc1f/download/64edd0ee-3d5d-43ce-8562-c336c24dbc1f.csv
