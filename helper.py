import json

with open('classes.txt', 'r') as f:
    classes = json.load(f)

options = []
for class_name in classes.keys():
    option = {
        "text": {
            "type": "plain_text",
            "text": class_name,
            "emoji": True
        },
        "value": class_name
    }
    options.append(option)
print()

def create_message(text, selected_options=None, threshold=None):
    if not threshold:
        threshold = '0.15'
    else:
        threshold = str(threshold)

    if selected_options:
        initial_options = []
        for option in selected_options:
            initial_option = {
                "text": {
                    "type": "plain_text",
                    "text": option,
                    "emoji": True
                },
                "value": option
            }
            initial_options.append(initial_option)


    message = {
        "text": "This is the FoodcamAlert Options Page",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "element": {
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select options",
                        "emoji": True
                    },
                    "options": options,
                    "action_id": "multi_static_select-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Food Options",
                    "emoji": True
                }
            },
            {
                "dispatch_action": False,
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "plain_text_input-action",
                    "initial_value": threshold,
                },
                "label": {
                    "type": "plain_text",
                    "text": "Detection Confidence Threshold",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": " "
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Update Preferences",
                        "emoji": True
                    },
                    "value": "click_me_123",
                    "action_id": "button-action"
                }
            }
        ]
    }
    if selected_options:
        message['blocks'][3]['element']['initial_options'] = initial_options

    return message
