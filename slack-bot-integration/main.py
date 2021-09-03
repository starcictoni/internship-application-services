import logging
from flask import Flask, request, jsonify, Response
from flask.logging import default_handler
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
import requests
import uuid
import tensorflow as tf
from tensorflow import keras
import tensorflow_text as text
import numpy as np
from env import BOT_TOKEN,SLACK_SIGNING_SECRET
from block_kit_templates import *
import db_connector

db_connector.setup_db()

model = keras.models.load_model("hj_model")

prediction_categories = ["OOD", "prijave stručne prakse", "prijave zavrsnog ili diplomskog rada", "upisa na sveuciliste"]

app = Flask(__name__)

bolt_app = App(token=BOT_TOKEN,signing_secret=SLACK_SIGNING_SECRET)
client = WebClient(token=BOT_TOKEN)

handler = SlackRequestHandler(bolt_app)

#Bot ID, in case we need it later
BOT_ID = client.api_call("auth.test")["user_id"]

@bolt_app.event("app_mention")
def app_mention(event):

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    thread_ts = event.get("ts")
    if event.get("thread_ts"):
        thread_ts = event.get("thread_ts")
    #This is the part where the actual intent will be calculated
    if f"<@{BOT_ID}> " in text:
        #Check if conversation already exists with this user in this specif thread
        conversation_history = db_connector.get_conversation_info(thread=thread_ts, user=user_id)

        if conversation_history:
            message_text = f'<@{user_id}> s vama već imam započetu konverzaciju u ovom threadu.\nVaša poruka je bila : {conversation_history.get("message")}. '
            response_message_to_dm = client.chat_postMessage(channel= channel_id, text=message_text, thread_ts=thread_ts)
            if conversation_history.get("predicted_intent") == "OOD":
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=f"Pošto nisam razumio vašu poruku napišite mi novu u ovaj thread bez <@{BOT_ID}>", thread_ts=thread_ts)
            else:
                additional_message_text = f'Ja sam predpostavio da želite pokrenut proces {conversation_history.get("predicted_intent")}.\nČekam vaš da ili ne odgovor  bez <@{BOT_ID}> na tu poruku.'
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=additional_message_text, thread_ts=thread_ts)
        else:
            #Get prediction from model
            results = model.predict(np.array([text]))
            max_result = np.argmax(results)
            prediction = prediction_categories[max_result]

            if prediction == "OOD":
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=f"Nisam razumio sto ste mislili pod : {text}. ", thread_ts=thread_ts)
            else:
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=f"Započinjem proces {prediction}, molim potvrdu s da/ne",thread_ts=thread_ts)

            #Add new conversation in database
            db_connector.add_conversation(thread_ts, user_id, text, prediction)
        

@bolt_app.event("message")
def thread_message(event):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    conversation_history = None

    #Check if message is in thread
    if thread_ts:
        #Get user conversation info
        conversation_history = db_connector.get_conversation_info(thread=thread_ts, user=user_id)
    
    if conversation_history:
        text = event.get("text")
        if f"<@{BOT_ID}> " in text:
            #Don't answer to app_mention events in thread
            return
        if conversation_history.get("predicted_intent") == "OOD":
            results = model.predict(np.array([text]))
            max_result = np.argmax(results)
            prediction = prediction_categories[max_result]
            
            if prediction == "OOD":
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=f"Nisam razumio sto ste mislili pod : {text}. ",thread_ts=thread_ts)
            else:
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text=f"Započinjem proces {prediction}, molim potvrdu s da/ne",thread_ts=thread_ts)
            
            #Update conversation with new message and intent
            db_connector.update_conversation_message_and_intent(thread_ts, user_id, text, prediction)
        else:
            text = text.lower()
            if text == "da":
                if conversation_history.get("predicted_intent") == "prijave stručne prakse":
                    #Create APP DM channel
                    response_new_dm = client.conversations_open(users=user_id)
                    new_channel_id = response_new_dm.get("channel")["id"]
                    
                    #Start proces on the engine
                    res = requests.post("http://0.0.0.0:8080/instance")
                    response_message_to_dm = client.chat_postMessage(channel= new_channel_id, text="Započet proces za prijavu prakse")
                    #This should be removed in the future, reason -> case specific
                    res_json = res.json()
                    instance_id = res_json.get("id")
                    res_task = requests.get(f"http://0.0.0.0:8080/instance/{instance_id}")
                    res_task_json = res_task.json()
                    task_id = res_task_json.get("pending")[0]
                    text_message = f"Trebate ispuniti formu na http://0.0.0.0/form/{instance_id}/{task_id}"
                    response_new_message_to_dm = client.chat_postMessage(channel= new_channel_id, text=text_message)
                    
                    response_message_to_dm = client.chat_postMessage(channel= channel_id, text="Super, javim ti se privatnom porukom uskoro. ",thread_ts=thread_ts)
                else:
                   response_message_to_dm = client.chat_postMessage(channel= channel_id, text="Trenutno nije implementiran taj proces.",thread_ts=thread_ts)
                
                #Save finished conversation into DB with True value for prediction result
                db_connector.finish_conversion(thread=thread_ts, user=user_id, prediction_result=True )
            elif text == "ne":
                response_message_to_dm = client.chat_postMessage(channel= channel_id, text="Nema frke, tu sam ako što treba.",thread_ts=thread_ts)
                #Save finished conversation into DB with False value for prediction result
                db_connector.finish_conversion(thread=thread_ts, user=user_id, prediction_result=False)
            else:
               response_message_to_dm = client.chat_postMessage(channel= channel_id, text="Odgovorite s da ili ne",thread_ts=thread_ts)


#THIS IS REQUIRED FOR EACH SLACK APP
@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@app.route("/notify/student/after/approval", methods=["POST"])
def notify_student():
    data = request.get_json()

    #Data for message    
    instance_id = str(data.get("id_instance"))
    task_id = str(data.get("next_task"))

    #Get student from params
    student_to_notify = request.args.get("to")
    #Get student id
    student_slack_id = get_users_slack_id(student_to_notify)
    #Make template
    template = student_after_approval_template(instance_id, task_id)
    #Send
    send_dm_with_template(student_slack_id, template)
    
    return jsonify(success=True)

@app.route("/notify/student/potvrda/pdf", methods=["POST"])
def notify_student_potvrda_pdf():
    data = request.get_json()

    #Data for message    
    instance_id = str(data.get("id_instance"))
    task_id = str(data.get("next_task"))
    attachment_url = data.get("attachment_url")
    #Get student from params
    student_to_notify = request.args.get("to")

    student_slack_id = get_users_slack_id(student_to_notify)
    
    template = student_potvrda_template(instance_id, task_id)

    send_dm_with_template(student_slack_id, template, attachment_url)
    

    return jsonify(success=True)


@app.route("/notify/student/after/allocation", methods=["POST"])
def notify_student_after_allocation():
    data = request.get_json()

    #Data for template
    kompanija = str(data.get("kompanija"))
    ime_poslodavac = str(data.get("ime_poslodavac"))
    email_poslodavac = str(data.get("poslodavac_email"))
    opis_posla = str(data.get("opis_posla"))

    student_to_notify = request.args.get("to")

    #Get student id    
    student_slack_id = get_users_slack_id(student_to_notify)
    #Create block template
    template = student_after_allocation_template(kompanija, ime_poslodavac, email_poslodavac, opis_posla)
    #Send
    send_dm_with_template(student_slack_id, template)    

    return jsonify(success=True)


def get_users_slack_id(email):
    #Get all users
    users_list_response = client.users_list()
    members = users_list_response.get("members")
    #Find student to notify
    for m in members:
        if email == m["profile"].get("email"):
            student_slack_id = m.get("id")
            return student_slack_id
    return None

def send_dm_with_template(user, template, attachment_url=None):
    response_new_dm = client.conversations_open(users=user)
    new_channel_id = response_new_dm.get("channel")["id"]
    response_message_to_dm = client.chat_postMessage(channel=new_channel_id, blocks=template)
    #Check for attachment url in data
    if attachment_url:
        external_id = uuid.uuid4()
        response_new_message_to_dm = client.chat_postMessage(channel=new_channel_id, text="Dostavljam vam potreban PDF")
        response_file_remote_add = client.files_remote_add(external_id=external_id,external_url=attachment_url,title="New attachment")
        response_file_remote_share = client.files_remote_share(channels=new_channel_id, external_id=external_id)







if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(default_handler)
    logger.addHandler(logging.StreamHandler())
    app.run(host="0.0.0.0",port=8090)
