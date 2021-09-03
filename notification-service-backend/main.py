import sendgrid
from sendgrid.helpers.mail import Mail,To, Attachment, FileContent, FileName, FileType, Disposition, ContentId
import aiohttp
from aiohttp import web
from urllib import parse
from env import *

SG = sendgrid.SendGridAPIClient(API_KEY)
#HEADER = {"Authorization": "Bearer "+API_KEY}


async def send_email(request, template_type, attachment_name="new.pdf"):
    data = await request.json()
    print(data)

    if request.query_string:
        query_dict = dict(parse.parse_qsl(request.query_string))
    else:
        #error -> to:email must be send via params
        pass
    

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=query_dict["to"],
    )

    message.dynamic_template_data = data

    if template_type == "student_after_approval": 
        message.template_id = STUDENT_AFTER_APPROVAL_TEMPLATE
    elif template_type == "student_after_allocation":
        message.template_id = STUDENT_AFTER_ALLOCATION_NOTIFICATION_TEMPLATE
    elif template_type == "poslodavac_after_allocation":
        message.template_id = POSLODAVAC_AFTER_ALLOCATION_NOTIFICATION_TEMPLATE
    elif template_type == "student_pdf":
        message.template_id = STUDENT_SEND_PDF_TEMPLATE
    
    if "attachment" in data:
        attachment = Attachment()
        attachment.file_content = FileContent(data["attachment"])
        attachment.file_type = FileType("application/pdf")
        attachment.file_name = FileName(attachment_name)
        attachment.disposition = Disposition("attachment")
        attachment.content_id = ContentId("Example Content ID")

        message.attachment = attachment
        

    try:
        SG.send(message)    
    except Exception as e:
        print(e)
    

async def send_email_student_pdf(request):
    #Specify template type
    template_type = "student_pdf"

    await send_email(request, template_type, attachment_name="potvrda_prakse.pdf")

    return web.json_response({"status": "OK"})

async def send_email_student_after_approval(request):
    #Specify template type
    template_type = "student_after_approval"
    
    await send_email(request, template_type)

    return web.json_response({"status":"OK"})


async def send_email_poslodavac_after_allocation(request):
    #Specify template type
    template_type = "poslodavac_after_allocation"
    
    await send_email(request, template_type)

    return web.json_response({"status":"OK"})


async def send_email_student_after_allocation(request):
    #Specify template type
    template_type = "student_after_allocation"

    await send_email(request, template_type)

    return web.json_response({"status":"OK"})


app = web.Application()
app.add_routes([web.post("/send/email/pdf/student", send_email_student_pdf)])
app.add_routes([web.post("/send/email/approval/student", send_email_student_after_approval)])
app.add_routes([web.post("/send/email/allocation/poslodavac", send_email_poslodavac_after_allocation)])
app.add_routes([web.post("/send/email/allocation/student", send_email_student_after_allocation)])
web.run_app(app,port=8081)