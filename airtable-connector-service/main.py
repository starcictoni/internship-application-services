import aiohttp
from aiohttp import web
import requests
from urllib import parse
import uuid
import aiohttp_cors

from env import API_KEY, BASE_ID

AIRTABLE_URL = "https://api.airtable.com/v0/"
GET_HEADER = {"Authorization":"Bearer "+ API_KEY}
POST_PATCH_HEADER = {"Authorization":"Bearer "+ API_KEY, "Content-Type": "application/json"}

async def post_student_after_selecting_assignments(request):
    data = await request.json()
    #Prepare data for last POST
    poslodavci = []
    student = []

    #Create new record in Studenti table
    table_name = "Studenti"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    if "JMBAG" and "ime_student" and "email_student" and "godina_studija" in data:
        data_to_post_fields = {"fields":{
            "JMBAG":data["JMBAG"],
            "ime_student":data["ime_student"],
            "email_student":data["email_student"],
            "godina_studija":data["godina_studija"]
        }}
    
    data_to_post_student = {"records":[data_to_post_fields]}
    
    post_student_response = requests.post(url, headers=POST_PATCH_HEADER, json=data_to_post_student)
    post_response_json = post_student_response.json()
    student_id = post_response_json["records"][0]["id"]
    #Save student id for last POST
    student.append(student_id)
    
    #Get all poslodavci ID
    table_name = "Poslodavci"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    get_poslodavci_response = requests.get(url, headers=GET_HEADER)
    get_response_json = get_poslodavci_response.json()
    poslodavci_records = get_response_json["records"]

    if "zeljeni_poslodavci" in data:
        for r in poslodavci_records:
            for p in data["zeljeni_poslodavci"]:
                if p == str(r["fields"]["oznaka_poslodavca"]):
                    #Save poslodavac id for last POST
                    poslodavci.append(r["fields"]["poslodavac_id"])

    print(poslodavci)

    #Last POST
    table_name = "Alociranje_studenata"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    data_to_post_fields = {"fields":{
        "napomena": data["napomena"],
        "jmbag_studenta":student,
        "odabrani_poslodavci": poslodavci
        
    }}
    data_to_post_alociranje = {"records":[data_to_post_fields]}

    response = requests.post(url, headers=POST_PATCH_HEADER, json=data_to_post_alociranje)

    #Return new student id as response
    data_response = []
    data_response.append({"student_id":student_id})

    return web.json_response(data_response)

async def get_assigned_poslodavac(request):
    data_response = []
    #Get poslodavac id from Alociranje_studenata
    table_name = "Alociranje_studenata"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    get_alociranje_response = requests.get(url, headers=GET_HEADER)
    get_alociranje_response_json = get_alociranje_response.json()
    get_alociranje_response_records = get_alociranje_response_json["records"]

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        if "student_id" in query_dict:
            for r in get_alociranje_response_records:
                if query_dict["student_id"] in str(r["fields"]["jmbag_studenta"][0]):
                    poslodavac_id = r["fields"]["alocirani_poslodavac"][0]

    #Get data from Poslodavci
    table_name = "Poslodavci"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    get_poslodavci_response = requests.get(url, headers=GET_HEADER)
    get_poslodavci_response_json = get_poslodavci_response.json()
    get_poslodavci_response_records = get_poslodavci_response_json["records"]

    for r in get_poslodavci_response_records:
        if poslodavac_id == str(r["id"]):
            data_response.append(r["fields"])

    return web.json_response(data_response)
    

async def poslodavci_array_oznaka_kompanija(request):
    table_name = "Poslodavci"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    response = requests.get(url, headers=GET_HEADER)
    airtable_response = response.json()
    airtable_records = airtable_response["records"]

    data_response = []

    for r in airtable_records:
        oznaka = r["fields"]["oznaka_poslodavca"]
        kompanija = r["fields"]["kompanija"]
        data_response.append(f"{oznaka},{kompanija}")
    
    return web.json_response(data_response)

async def handle_patch_student(request):
    table_name = "Studenti"
    
    data = await request.json()
    
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        if "student_id" in query_dict:
            student_id = query_dict["student_id"]

    if "poslodavac_id" in data:
        data["trenutni_poslodavac"] = [data["poslodavac_id"]]
        del data["poslodavac_id"]


    data_to_patch = {
        "records":[{
            "id": student_id,
            "fields": data
        }]
    }


    print(data_to_patch)

    response = requests.patch(url, headers=POST_PATCH_HEADER, json=data_to_patch)
    
    print(response.raw)
    print(response.reason)
    print(response.status_code)

    return web.json_response({"status":response.status_code})

async def handle_patch_student_pdf(request):
    table_name = "Studenti"
    url = AIRTABLE_URL + BASE_ID + "/" + table_name

    data = await request.json()

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
        
        if (("potvrda_attachment" in data and "dnevnik_attachment" in data) and "student_id" in query_dict):
            data_to_patch = {
                "records":[
                    {
                        "id":query_dict["student_id"],
                        "fields":{
                            "potvrda_prakse":[
                                {"url":data["potvrda_attachment"]}
                            ],
                            "dnevnik_prakse":[
                                {"url":data["dnevnik_attachment"]}
                            ],
                            "potvrda_prakse_url":data["potvrda_attachment"],
                            "dnevnik_prakse_url":data["dnevnik_attachment"],
                            "nastavak_rada":data["nastavak_rada"]
                        }
                    }
                ]
            }
            print(data_to_patch)
            response = requests.patch(url, headers=POST_PATCH_HEADER, json=data_to_patch)
            print(response.reason)
    return web.json_response({"status":response.status_code})


app = web.Application()
app.add_routes([web.get("/get/assigned/poslodavac", get_assigned_poslodavac)])
app.add_routes([web.get("/poslodavci/array/oznaka/kompanija", poslodavci_array_oznaka_kompanija)])
app.add_routes([web.patch("/student/prihvacen", handle_patch_student)])
app.add_routes([web.patch("/student/patch/pdf", handle_patch_student_pdf)])
app.add_routes([web.post("/post/student/after/selecting/assignments", post_student_after_selecting_assignments)])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)


web.run_app(app, port=8082)