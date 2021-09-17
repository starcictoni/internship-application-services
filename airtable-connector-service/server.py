import aiohttp
from aiohttp import web
import requests
from urllib import parse
import os
import aiohttp_cors
import datetime as dt

from env import API_KEY, BASE_ID

AIRTABLE_URL = "https://api.airtable.com/v0/"
GET_HEADER = {"Authorization": "Bearer " + API_KEY}
POST_PATCH_HEADER = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json",
}

routes = web.RouteTableDef()


def get_url_from_table_name(table_name):
    return os.path.join(AIRTABLE_URL, BASE_ID, parse.quote(table_name))


@routes.post("/post/student/after/selecting/assignments")
async def post_student_after_selecting_assignments(request):
    data = await request.json()
    # Prepare data for last POST
    poslodavci = []
    student = []

    # Create new record in Studenti table
    url = get_url_from_table_name("Studenti - preferencije")

    print(data)

    data_to_post = {
        "JMBAG": data["JMBAG"],
        "Ime i prezime": data["ime_student"],
        "E-mail": data["email_student"],
        "Godina studija": [data["godina_studija"]],
    }

    zadaci_req = requests.get(
        get_url_from_table_name("Poduzeća prijava prakse"),
        headers=GET_HEADER,
        params={"fields": ["ID zadatka", "Broj slobodnih mjesta"]},
    )

    zadaci = {
        r["ID zadatka"].split("-")[0].strip(): r
        for r in [{"id": r["id"], **r["fields"]} for r in zadaci_req.json()["records"]]
    }

    odabir_mapping = ["Prvi odabir", "Drugi odabir", "Treći odabir"]
    pids = [p.split("-")[0].strip() for p in data["zeljeni_poslodavci"]]

    for i, p in enumerate(pids):
        data_to_post[odabir_mapping[i]] = [zadaci[p]["id"]]

    data_to_post_student = {"records": [{"fields": data_to_post}]}

    post_response = requests.post(
        url, headers=POST_PATCH_HEADER, json=data_to_post_student
    )
    post_response_json = post_response.json()

    if "error" in post_response_json:
        raise Exception(post_response_json)

    student_id = post_response_json["records"][0]["id"]

    post_response = requests.post(
        get_url_from_table_name("Alokacija"),
        headers=POST_PATCH_HEADER,
        json={
            "records": [
                {
                    "fields": {
                        "Student": [student_id],
                        "process_instance_id": data.get("id_instance"),
                        "frontend_url": data.get("_frontend_url"),
                    }
                }
            ]
        },
    )

    if "error" in post_response_json:
        raise Exception(post_response_json)

    post_response_json = post_response.json()
    allocation_id = post_response_json["records"][0]["id"]

    return web.json_response({"student_id": student_id, "alokacija_id": allocation_id})


@routes.get("/get/assigned/poslodavac")
async def get_assigned_poslodavac(request):
    # Get poslodavac id from Alociranje_studenata
    url = get_url_from_table_name("Alokacija")

    response = requests.get(url, headers=GET_HEADER).json()
    records = response["records"]

    if request.query_string:
        query_dict = dict(request.query)
        if "student_id" in query_dict:
            for r in records:
                if query_dict["student_id"] == r["fields"]["Student"][0]:
                    poslodavac_id = r["fields"]["Alokacija"][0]

    # Get data from Poslodavci
    table_name = "Poduzeća prijava prakse"
    response = requests.get(
        get_url_from_table_name(table_name), headers=GET_HEADER
    ).json()
    records = response["records"]

    data_response = {}
    for r in records:
        f = r["fields"]
        if poslodavac_id == r["id"]:
            data_response = {
                "poslodavac_email": f["Kontakt mail"],
                "kompanija": f["Naziv"][0],
                "opis_posla": f["Zadatak studenta"],
                "poslodavac_id": f["Poduzeće"][0],
            }

    return web.json_response(data_response)


@routes.get("/poslodavci/array/oznaka/kompanija")
async def poslodavci_array_oznaka_kompanija(request):
    table_name = "Poduzeća prijava prakse"
    url = os.path.join(AIRTABLE_URL, BASE_ID, parse.quote(table_name))

    response = requests.get(
        url,
        headers=GET_HEADER,
        params={
            "fields": ["ID zadatka", "Naziv poduzeća", "Broj slobodnih mjesta"],
            "view": "Slobodni zadaci",
        },
    )

    airtable_response = response.json()
    airtable_records = airtable_response["records"]

    data_response = []

    for r in airtable_records:
        f = r["fields"]
        data_response.append(f"{f['ID zadatka']} ({f['Broj slobodnih mjesta']} mjesta)")

    return web.json_response(data_response)


@routes.patch("/student/prihvacen")
async def handle_patch_student(request):

    table_name = "Prijavnice"
    data = await request.json()
    url = os.path.join(AIRTABLE_URL, BASE_ID, parse.quote(table_name))

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        if "student_id" in query_dict:
            data["Student"] = [query_dict["student_id"]]

    print(request.query_string)
    print(data)

    record = {
        "Poduzeće": [data["Poduzeće"]],
        "datum_zavrsetka": dt.datetime.strptime(data["datum_zavrsetka"], "%d/%m/%Y")
        .date()
        .isoformat(),
        "datum_pocetka": dt.datetime.strptime(data["datum_pocetka"], "%d/%m/%Y")
        .date()
        .isoformat(),
    }
    del data["_frontend_url"]

    record = {**data, **record}

    data_to_patch = {"records": [{"fields": record}]}

    print(data_to_patch)

    response = requests.post(url, headers=POST_PATCH_HEADER, json=data_to_patch)

    prijavnica_id = response.json()["records"][0]["id"]

    print(response.status_code)
    print(response.text)

    return web.json_response(
        {
            "status": response.status_code,
            "reason": response.reason,
            "message": response.text,
            "prijavnica_id": prijavnica_id,
        },
        status=response.status_code,
    )


@routes.patch("/student/patch/pdf")
async def handle_patch_student_pdf(request):
    table_name = "Dnevnik prakse"
    url = os.path.join(AIRTABLE_URL, BASE_ID, parse.quote(table_name))

    data = await request.json()

    response = None

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        data_to_patch = {
            "records": [
                {
                    "fields": {
                        "Student": [query_dict["prijavnica_id"]],
                        "Potvrda": [{"url": data["potvrda_attachment"]}],
                        "Dnevnik": [{"url": data["dnevnik_attachment"]}],
                        # "potvrda_prakse_url": data["potvrda_attachment"],
                        # "dnevnik_prakse_url": data["dnevnik_attachment"],
                        "Suradnja": True if data["nastavak_rada"] != "" else False,
                    },
                }
            ]
        }
        print(data_to_patch)
        response = requests.post(url, headers=POST_PATCH_HEADER, json=data_to_patch)
        print(response.text)

    return web.json_response(
        {"status": response.status_code, "message": response.text},
        status=response.status_code,
    )


app = None


def run():
    global app

    app = web.Application()
    app.add_routes(routes)
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    return app


async def serve():
    return run()


if __name__ == "__main__":
    app = run()
    web.run_app(app, port=8082)
