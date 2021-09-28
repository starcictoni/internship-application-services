from env import API_KEY, BASE_ID
import os
import urllib
import requests

AIRTABLE_URL = "https://api.airtable.com/v0/"
AUTH_HEADER = {"Authorization": "Bearer " + API_KEY}
GET_HEADER = AUTH_HEADER
POST_PATCH_HEADER = {
    **AUTH_HEADER,
    "Content-Type": "application/json",
}


def get_table_url(table_name, id=None):
    if id:
        return os.path.join(AIRTABLE_URL, BASE_ID, urllib.parse.quote(table_name), id)
    else:
        return os.path.join(AIRTABLE_URL, BASE_ID, urllib.parse.quote(table_name))


def post(table, data):
    if not isinstance(data, list):
        data = [data]

    check_fields = lambda x: {"fields": x} if "fields" not in x else x
    data = list(map(check_fields, data))

    url = get_table_url(table)

    r = requests.post(url, headers=POST_PATCH_HEADER, json={"records": data})
    if r.status_code not in (200, 201):
        raise Exception(r.text)

    return _handle_record_response(r)


def _handle_record_response(r):
    if r.status_code == 200:
        data = r.json()
        unpack = lambda x: {
            "_id": x["id"],
            "_createdTime": x["createdTime"],
            **x["fields"],
        }
        if "records" in data:
            return list(map(unpack, data["records"]))
        elif "fields" in data:
            return [unpack(data)]
    else:
        raise Exception(r.text)
    return None


def get_one(table, id=None, fields=None, view=None, filter=None, params={}):
    data = get(table, id, fields, view, filter, params)
    if data and len(data) > 0:
        return data[0]
    return None


def get(table, id=None, fields=None, view=None, filter=None, params=None):
    if not params:
        params = {}
    if fields:
        params["fields"] = fields
    if view:
        params["view"] = view
    if filter:
        params["filterByFormula"] = filter

    url = get_table_url(table, id)
    r = requests.get(url, headers=GET_HEADER, params=params)

    return _handle_record_response(r)


if __name__ == "__main__":
    if False:
        data = get(
            "Poduzeća prijava prakse",
            fields=["ID zadatka", "Naziv poduzeća", "Broj slobodnih mjesta"],
            view="Slobodni zadaci",
        )
        print(len(data), "records...")
        print(data[0])
    if False:
        data = get_one(
            "Poduzeća prijava prakse",
            fields=["ID zadatka", "Naziv poduzeća", "Broj slobodnih mjesta"],
            view="Slobodni zadaci",
            filter="({ID zadatka} = 'Zadatak 69 - Red Martyr Entertainment')",
        )
        print(data)
    if False:
        data = get(
            "Poduzeća prijava prakse",
            fields=["ID zadatka", "Broj slobodnih mjesta"],
        )
        print(data[0])
    if False:
        data = get_one("Poduzeća prijava prakse", "reco6IIUAMZotKfjW")
        print(data)
    if False:
        data = post("Alokacija", {"Student": ["recClX5RC769nx9Yk"]})
        print(data)
    if True:
        data = get("Alokacija")
        print(data)
