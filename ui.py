from getpass import getpass

import json
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def get_vk_creds():
    creds = None
    with open('./vk_creds.json', "r") as write_file:
        creds = json.load(write_file)
    login = creds['login']
    password = creds['password']
    if creds['login'] is None or len(creds['login']) == 0:
        login = input('Enter VK login: ')
    if creds['password'] is None or len(creds['password']) == 0:
        password = getpass('Enter VK password: ')
    return login, password

def auth_vk_handler():
    key = input("Enter VK authentication code: ")
    remember_device = True
    return key, remember_device

def get_user_channel_select(channels):
    for case in [f'{ch}: {channels[ch]["name"]}' for ch in channels]:
        print(case)
    channel_index = int(input("Enter index: "))
    print(f'Selected channel is: {channels[channel_index]["name"]}')
    return channels[channel_index]