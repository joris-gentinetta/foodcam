# Description

This is a Slack bot that continuously monitors a webcam in the MIT Media Lab where leftover food from events is placed. Authorized users can send it a message and subscribe to their favourite foods to get notifications. The bot is based on a classification model trained on the Food-101 dataset. 


# Installation

- Create a conda environment: ```conda create -n foodcam_bot python=3.8```
- Activate the environment: ```conda activate foodcam_bot```
- Install PyTorch for your system: https://pytorch.org/get-started/locally/
- Install the required packages: ```pip install -r requirements.txt```