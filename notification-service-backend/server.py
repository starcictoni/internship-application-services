import sendgrid
import base64
from sendgrid.helpers.mail import (
    Mail,
    To,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
    ContentId,
    DynamicTemplateData,
)
import requests
import env
from aiohttp import web
from urllib import parse
from env import *

SG = sendgrid.SendGridAPIClient(API_KEY)
# HEADER = {"Authorization": "Bearer "+API_KEY}


routes = web.RouteTableDef()


async def send_email(request, template_type):
    data = await request.json()

    if request.query_string:
        query_dict = dict(request.query)
    else:
        # error -> to:email must be send via params
        pass

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=query_dict["to"],
    )

    if template_type == "student_after_approval":
        message.template_id = STUDENT_AFTER_APPROVAL_TEMPLATE
    elif template_type == "student_after_allocation":
        message.template_id = STUDENT_AFTER_ALLOCATION_NOTIFICATION_TEMPLATE
    elif template_type == "poslodavac_after_allocation":
        message.template_id = POSLODAVAC_AFTER_ALLOCATION_NOTIFICATION_TEMPLATE
    elif template_type == "student_pdf":
        message.template_id = STUDENT_SEND_PDF_TEMPLATE

    message.dynamic_template_data = DynamicTemplateData(data)

    if "attachment_url" in data:
        file_handle = requests.get(data["attachment_url"])
        encoded_pdf = base64.b64encode(file_handle.content).decode()

        attachment = Attachment()
        attachment.file_content = FileContent(encoded_pdf)
        attachment.file_type = FileType("application/pdf")
        attachment.file_name = FileName(data["attachment_name"])
        attachment.disposition = Disposition("attachment")
        attachment.content_id = ContentId("Example Content ID")

        message.attachment = attachment

    try:
        SG.send(message)
    except Exception as e:
        print(e)


@routes.post("/send/email/pdf/student")
async def send_email_student_pdf(request):
    # Specify template type
    template_type = "student_pdf"

    await send_email(request, template_type, attachment_name="potvrda_prakse.pdf")

    return web.json_response({"status": "OK"})

@routes.get("/status")
async def status(request):
    return web.json_response({"status": "OK"})    

@routes.post("/email")
async def send_plain_email(request):
    query_dict = dict(request.query)
    await send_email(request, query_dict.get("template"))
    return web.json_response({"status": "OK"})


@routes.get("/meta")
async def get_meta(request):
    meta_routes = []
    for r in routes:
        if r.path != '/meta':
            route = {
                "method": r.method,
                "url": r.path
            }
            meta_routes.append(route)
    return web.json_response(meta_routes)

app = None


def run():
    global app

    app = web.Application()
    app.add_routes(routes)

    return app


async def serve():
    return run()


if __name__ == "__main__":
    app = run()
    web.run_app(app, host='127.0.0.1', port=8081)
