# Slackbot service

This is example of slackbot service that uses Tensorflow model for intent recognition using which it is able to have conversation with the user and start specific process on Python BPMN engine. It uses DB for storing active conversations and predicted intent for each message.

## Installation 
```
pip install -r requirements.txt
```

You will need to create `env.py` in which you will store your Bot token and Slack signing secret.

```python
BOT_TOKEN = "xxxxxxxxxxxxx"
SLACK_SIGNING_SECRET = "xxxxxxxxxxxxx"
```

For bot to function properly you will need give it following OAuth Scopes :
- app_mentions:read
- channels:history
- channels:manage
- chat:write
- groups:write
- im:read
- im:write
- remote_files:share
- remote_files:write
- users:read
- users:read.email

Although at the moment bot is not using some of the scopes specified above it will in the future.

## Usage

You will need to install bot into your Slack workspace and give it a name after which you will have to put it inside channels you want him to operate.

### Note

Inside `block_kit_template.py` you can find examples of templates that bot can use in conversation. As those examples are case specific they might not be of use but they provide idea how to construct such template.