from aiohttp import web
import requests
from urllib import parse
import os
import aiohttp_cors
import datetime as dt
import airtable as at

routes = web.RouteTableDef()


@routes.post("/student-preference")
async def post_student_after_selecting_assignments(request):
    data = await request.json()

    data_to_post = {
        "JMBAG": data["JMBAG"],
        "Ime i prezime": data["ime_student"],
        "E-mail": data["email_student"],
        "Godina studija": [data["godina_studija"]],
        "Napomena": data["napomena"],
    }

    zadaci_data = at.get(
        "Poduzeća prijava prakse",
        fields=["ID zadatka", "Broj slobodnih mjesta"],
    )

    zadaci = {r["ID zadatka"].split("-")[0].strip(): r for r in zadaci_data}

    odabir_mapping = ["Prvi odabir", "Drugi odabir", "Treći odabir"]
    pids = [p.split("-")[0].strip() for p in data["zeljeni_poslodavci"]]

    for i, p in enumerate(pids):
        data_to_post[odabir_mapping[i]] = [zadaci[p]["_id"]]

    post_response = at.post("Studenti - preferencije", data_to_post)
    student_id = post_response[0]["_id"]

    post_response = at.post(
        "Alokacija",
        {
            "Student": [student_id],
            "process_instance_id": data.get("id_instance"),
            "frontend_url": data.get("_frontend_url"),
        },
    )

    allocation_id = post_response[0]["_id"]

    return web.json_response({"student_id": student_id, "alokacija_id": allocation_id})

@routes.get("/meta")
async def meta(request):
    get_routes = []
    get_object = {}
    for r in routes:
            get_object = {
                "method": "GET",
                "url": r.path
            }
            get_routes.append(get_object)
    return web.json_response(get_routes)

@routes.get("/status")
async def status(request):
    return web.json_response({"status": "OK"})   

@routes.get("/allocation")
#@service_task("Meta podaci") Treba definirati svoje dekoratore, pa nek filtrira servise na temelju toga, ovisno o mjestu odakle se poziva, pr. iz user taska za GET
async def handle_get_allocation(request):

    response = at.get("Alokacija")
    query_dict = dict(request.query)
    if "student_id" in query_dict:
        for r in response:
            if query_dict["student_id"] == r["Student"][0]:
                poslodavac_id = r["Alokacija"][0]

    pod = at.get_one("Poduzeća prijava prakse", poslodavac_id)
    data_response = {
        "poslodavac_email": pod["Kontakt mail"],
        "kompanija": pod["Naziv"][0],
        "opis_posla": pod["Zadatak studenta"],
        "poslodavac_id": pod["Poduzeće"][0],
    }

    return web.json_response(data_response)

@routes.get("/praksa-zadaci")
#@autocomplete("Dostupni zadaci")
async def handle_get_zadaci(request):
    response = at.get(
        "Poduzeća prijava prakse",
        fields=["ID zadatka", "Naziv poduzeća", "Broj slobodnih mjesta"],
        view="Slobodni zadaci",
    )

    data_response = [
        f"{r['ID zadatka']} ({r['Broj slobodnih mjesta']} mjesta)" for r in response
    ]

    return web.json_response(data_response)

@routes.post("/prijavnica")
async def handle_post_prijavnica(request):
    data = await request.json()

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        if "student_id" in query_dict:
            data["Student"] = [query_dict["student_id"]]

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

    response = at.post("Prijavnice", record)
    prijavnica_id = response[0]["_id"]

    return web.json_response(
        {
            "status": "ok",
            "prijavnica_id": prijavnica_id,
        }
    )

@routes.post("/dnevnik")
async def handle_post_dnevnik(request):
    data = await request.json()
    try:
        if request.query_string:
            query_dict = dict(parse.parse_qsl(request.query_string))
            post_data = {
                "Student": [query_dict["prijavnica_id"]],
                "Potvrda": [{"url": data["potvrda_attachment"]}],
                "Dnevnik": [{"url": data["dnevnik_attachment"]}],
                "Suradnja": True if data["nastavak_rada"] != "" else False,
            }
            print(post_data)
            response = at.post("Dnevnik prakse", post_data)
        return web.json_response(
            {"status": "ok", "id": response[0]["_id"]},
        )
    except Exception:
        return web.json_response({"status": "error"}, status=500)



app = None


def run():
    global app
    ws = web.WebSocketResponse(autoping=True, )
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
    web.run_app(app, host='127.0.0.1', port=8082)
