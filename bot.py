import json
import logging
import os
import pprint
import threading
import time
import keyring
from datetime import datetime
from io import BytesIO
import numpy as np

import requests
from PIL import Image
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from transformers import pipeline

from helper import create_message

STREAM_URL = "http://foodcam.media.mit.edu/axis-cgi/mjpg/video.cgi?1710353936070"
os.environ["SLACK_APP_TOKEN"] = keyring.get_password("slack", "slack_app_token")
os.environ["SLACK_BOT_TOKEN"] = keyring.get_password("slack", "slack_bot_token")

logging.basicConfig(filename='logs.txt', level=logging.INFO)
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
userbase = {}


def generate_message(user_id):
    if user_id in userbase.keys():
        selected_options = userbase[user_id]['selected_options']
        threshold = userbase[user_id]['threshold']
        text = f"Hi <@{user_id}>! Your current settings are: \n" + f'Food Options: {selected_options}\n' + f'Detection Confidence Threshold: {threshold}. You can change them below.'
    else:
        text = f"Hi <@{user_id}>! This is the FoodcamAlert bot. You can choose your favourite foods in the box below and I'll send you a message whenever I detect them on the foodcam. I contiuously monitor the cam, so that you can secure your snack even bevore the button is pressed. Please also let me know the detection confidence threshold above which you would like to be notified (range: [0.1, 1]). I recommend to start with 0.15 and raise it if you get too many false alerts."
    return create_message(text)


@app.message()
def message_hello(message, say):
    # say(f"Hey there <@{message['user']}>!")
    say(generate_message(message['user']))


@app.action("button-action")
def save_button(ack, body, logger, say):
    print('save_button')
    selected_options = 'nope'
    threshold = 'nope'
    user_id = body['user']['id']
    user = body['user']['name']
    username = body['user']['username']
    for value in body['state']['values'].values():
        if 'multi_static_select-action' in value.keys():
            selected_options = [selection['text']['text'] for selection in
                                value['multi_static_select-action']['selected_options']]
        else:
            threshold = value[list(value.keys())[0]]['value']
    if selected_options == 'nope' or threshold == 'nope':
        logger.info('Something went wrong, could not find the selected options or threshold')
        exit()
    if threshold is not None:
        try:
            threshold = float(threshold)
        except:
            threshold = -1
        if threshold < 0.1 or threshold > 1:
            say('Threshold must be between 0.1 and 1. Please try again.')
        else:
            say('Preferences saved. These are your current settings: \n' + f'Food Options: {selected_options}\n' + f'Detection Confidence Threshold: {threshold}')
            userbase[user_id] = {'selected_options': selected_options, 'threshold': threshold, 'user': user, 'username': username, 'reported': False}
    else:
        say('Please enter a threshold between 0.1 and 1')

    with open('userbase.json', 'w') as f:
        json.dump(userbase, f, indent=4)

    ack()
    logger.info(body)


@app.action("multi_static_select-action")
def food_selection(ack, body, logger):
    print('food_selection')
    ack()
    logger.info(body)


@app.action("plain_text_input-action")
def threshold_input(ack, body, logger):
    print('threshold_input')
    ack()
    logger.info(body)


def image_to_bytes(image):
    byte_arr = BytesIO()
    image.save(byte_arr, format='JPEG')
    return byte_arr.getvalue()


def capture_frame(stream_url):
    response = requests.get(stream_url, stream=True)
    bytes = b''
    for chunk in response.iter_content(chunk_size=1024):
        bytes += chunk
        a = bytes.find(b'\xff\xd8')
        b = bytes.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b + 2]
            image = Image.open(BytesIO(jpg))
            return image
    return None


def send_message(user_id, client, label, confidence, image):
    channel = app.client.conversations_open(users=user_id)["channel"]["id"]
    client.files_upload(
        channels=channel,
        initial_comment=f"There's {label}! Confidence: {confidence}",
        filename="foodcam",
        content=image,
        username="FoodCamAlert")


def process_webcam():
    pipe = pipeline("image-classification", model="nateraw/food")
    while True:
        frame = capture_frame(STREAM_URL)
        if frame:
            cropped = Image.fromarray(np.array(frame)[147: 433])
            results = pipe(cropped)
            current_time = datetime.now()
            print(current_time.strftime('%H:%M:%S'))
            pprint.pprint(results)
            print()
            save = False
            found_something = False
            for result in results:
                if result['score'] >= 0.08:
                    found_something = True
                for user_id in userbase.keys():
                    if result['label'] in userbase[user_id]['selected_options'] and result['score'] >= userbase[user_id]['threshold']:
                        if userbase[user_id]['reported'] == False:
                            save = True
                            userbase[user_id]['reported'] = True
                            send_message(user_id, app.client, result['label'], result['score'], image_to_bytes(frame))
            if save:
                try:
                    dirname = f"data/{current_time.strftime('%Y%m%d')}/{current_time.strftime('%H%M%S')}"
                    os.makedirs(dirname, exist_ok=True)
                    frame.save(f"{dirname}/frame.jpg")
                    with open(f"{dirname}/results.txt", "w") as f:
                        f.write(str(results))
                except Exception as e:
                    logging.error(f"Error saving frame: {e}")
            if not found_something:
                for user_id in userbase.keys():
                    userbase[user_id]['reported'] = False

        time.sleep(5)

if __name__ == "__main__":
    try:
        with open('userbase.json', 'r') as f:
            userbase = json.load(f)
    except:
        userbase = {}

    threading.Thread(target=SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start).start()
    threading.Thread(target=process_webcam).start()