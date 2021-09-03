from pony.orm import *
import os

DB = Database()

class Conversation(DB.Entity):
    thread = Required(str)
    user = Required(str)
    finished = Required(bool)
    intent = Optional("ConversationIntent")

class ConversationIntent(DB.Entity):
    message = Required(str)
    predicted_intent = Required(str)
    prediction_result = Optional(bool)
    conversation = Required("Conversation")



def setup_db():
    if not os.path.isdir("database"):
        os.mkdir("database")
    DB.bind(provider = "sqlite", filename="database/database.sqlite", create_db=True)
    DB.generate_mapping(create_tables=True)

@db_session
def add_conversation(thread, user, message, predicted_intent):
    conversation = Conversation(thread=thread, user=user, finished=False)
    conversation_intent = ConversationIntent(message=message, predicted_intent=predicted_intent, conversation=conversation)
    conversation.intent = conversation_intent

@db_session
def get_conversation_info(thread, user):
    print("Thread u db_connectoru : ", thread)
    open_conversation = Conversation.get(thread=thread, user=user, finished=False)
    if open_conversation:
        info = {}
        info["thread"] = open_conversation.thread
        info["user"] = open_conversation.user
        info["predicted_intent"] = open_conversation.intent.predicted_intent
        info["message"] = open_conversation.intent.message

        return info
    else:
        return None

@db_session
def update_conversation_message_and_intent(thread, user, message, predicted_intent):
    old_conversation = Conversation.get(thread=thread, user=user, finished=False)
    #Update message and intent
    old_conversation.intent.message = message
    old_conversation.intent.predicted_intent = predicted_intent

@db_session
def finish_conversion(thread, user, prediction_result):
    conversation = Conversation.get(thread=thread, user=user, finished=False)
    conversation.finished = True
    conversation.intent.prediction_result = prediction_result
