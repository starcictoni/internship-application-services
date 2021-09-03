import aiohttp
from aiohttp import web
import aiohttp_cors
import os

if not os.path.isdir("public"):
    os.mkdir("public")

#Handler for bytes file, eg. direct upload from attachment control in form
async def handle_post_file(request):
    reader = aiohttp.MultipartReader.from_response(request)

    metadata = None
    filename = None

    while True:
        part = await reader.next()
        if part is None:
            break
        if ".pdf" in part.filename:
            filename = part.filename
            metadata = await part.read()
            new_pdf = open("public/"+filename, "wb")
            new_pdf.write(metadata)
            print(f"Received {filename}, created new file at public/{filename}")
    
    return web.json_response({"status":"ok"})


app = web.Application()
app.add_routes([web.post("/post/file", handle_post_file)])
app.add_routes([web.static("/public", "./public")])

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

web.run_app(app, port=8084)