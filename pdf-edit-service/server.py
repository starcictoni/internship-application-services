from PyPDF2 import PdfFileWriter, PdfFileReader
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import aiohttp
from aiohttp import web
import aiohttp_cors
from urllib import parse
import base64
from hashlib import blake2b

pdfmetrics.registerFont(TTFont("OpenSans", "OpenSans-Regular.ttf"))

routes = web.RouteTableDef()


@routes.post("/potvrda/praksa")
async def generate_potvrda(request):
    data = await request.json()
    print(data)

    packet = io.BytesIO()

    can = canvas.Canvas(packet, pagesize=letter)
    can.setFillColorRGB(0, 0, 0)

    can.setFont("OpenSans", 12)

    if "ime_student" in data:
        # x -> left/right , y -> up/down
        can.drawString(160, 720, data["ime_student"])
    if "kompanija" in data:
        can.drawString(160, 658, data["kompanija"])
    if "ime_poslodavac" in data:
        can.drawString(160, 635, data["ime_poslodavac"])
    if "pocetak_prakse" in data:
        can.drawString(160, 613, data["pocetak_prakse"])
    if "kraj_prakse" in data:
        can.drawString(285, 613, data["kraj_prakse"])
    if "dogovoreni_broj_sati" in data:
        can.drawString(160, 590, str(data["dogovoreni_broj_sati"]))
    if "mentor" in data:
        can.drawString(160, 635, data["mentor"])
    if "detaljni_opis_zadatka" in data:
        start_y = 566
        num_of_chars = 50
        rich_text = data["detaljni_opis_zadatka"]
        slice_rich_text = []
        start_postions = {}
        remove_beginning = 0
        for i in range(0, len(rich_text), num_of_chars):
            current_text = rich_text[i : i + num_of_chars]
            slice_rich_text.append(current_text)
            start_postions[current_text] = i
        for s in slice_rich_text:
            without_beginning = None
            last_word_in_row = s.split()[-1]
            location_of_last_word_in_row = s.rfind(last_word_in_row) + start_postions[s]
            slice_of_text_after_last_word = rich_text[
                s.rfind(s.split()[-1]) + start_postions[s] :
            ]
            complete_last_word = slice_of_text_after_last_word.split()[0]
            if remove_beginning != 0:
                without_beginning = s[remove_beginning:]
            if last_word_in_row != complete_last_word:
                new_string = s[0 : location_of_last_word_in_row - start_postions[s]]
                if without_beginning:
                    without_beginning = without_beginning[
                        0 : location_of_last_word_in_row
                        - start_postions[s]
                        - remove_beginning
                    ]
                    s = without_beginning + complete_last_word
                else:
                    s = new_string + complete_last_word
                remove_beginning = len(complete_last_word) - len(last_word_in_row)
            else:
                if remove_beginning != 0:
                    s = without_beginning
                remove_beginning = 0

            can.drawString(160, start_y, s)
            start_y -= 18
    if "oib" in data:
        can.drawString(408, 718, str(data["oib"]))
    if "email_student" in data:
        can.setFont("OpenSans", 10)
        can.drawString(160, 697, data["email_student"])
    if "mobitel" in data:
        can.drawString(160, 682, data["mobitel"])

    can.save()

    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    existing_pdf = PdfFileReader(open("prijavnica_template.pdf", "rb"))
    output = PdfFileWriter()

    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)

    # Make hash of oib + ime_student for file name
    hash_blake2b = blake2b(digest_size=18)
    hash_blake2b.update(bytes(str(data["oib"]) + data["ime_student"], encoding="utf-8"))
    final_hash = hash_blake2b.hexdigest()

    pdf_name = f"{final_hash}.pdf"

    outputStream = open("public/" + pdf_name, "wb")
    output.write(outputStream)
    outputStream.close()

    # with open("public/" + pdf_name, "rb") as f:
    #     pdf_data = f.read()
    #     f.close()
    # encoded_pdf = base64.b64encode(pdf_data).decode()

    response = {
        # "attachment": encoded_pdf,
        "attachment_url": "http://0.0.0.0:8083/public/"
        + pdf_name,
    }

    return web.json_response(response)


if not os.path.exists("public"):
    os.makedirs("public")

app = None


def run():
    global app

    app = web.Application()
    app.add_routes(routes)
    app.add_routes([web.static("/public", "./public")])

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
    web.run_app(app, port=8083)
