import asyncio
import time
from pprint import pprint
from pathlib import Path
from shutil import rmtree
import copy

import json

import os

from creds import app_id, app_hash, app_name, vk_login, vk_password, vk_group_id
from telethon.sync import TelegramClient

from vk import VkPublicPoster


def clear_media():
    if not os.path.isdir('media'):
        os.makedirs('./media')
    [f.unlink() for f in Path("./media").glob("*") if f.is_file()]
    for path in Path("./media").glob("**/*"):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            rmtree(path)


async def get_channels_dict(client):
    channels = {}
    i = 1
    async for dialog in client.iter_dialogs():
        if not dialog.is_group and dialog.is_channel:
            channels[i] = {
                'name': dialog.name,
                'dialog': dialog
            }
            i += 1
    return channels


# 21784062
async def print_chanels(client):
    async for dialog in client.iter_dialogs():
        if not dialog.is_group and dialog.is_channel:
            index = 0
            print(dialog.name)
            async for message in client.iter_messages(dialog):
                print(message.text)
                if message.media:
                    if message.photo:
                        print('photo')
                    if message.video:
                        print('video')
                    # path = await message.download_media('./media')
                    # print('File saved to', path)  # printed safter download is done
                print('___')
                if index >= 2:
                    break
                index += 1
            print('<<<<<<>>>>>>')
    return

def save_last_id(dialog_id, last_msg_id):
    data = {}
    if not os.path.isdir('temp_data'):
        os.makedirs('./temp_data')
    else:
        with open("./temp_data/posted.json", "r") as read_file:
            data = json.load(read_file)
    data[dialog_id] = last_msg_id
    with open("./temp_data/posted.json", "w") as write_file:
        json.dump(data, write_file)

def get_last_msg_id(dialog_id):
    if not os.path.isdir('temp_data'):
        return 0
    with open("./temp_data/posted.json", "r") as read_file:
        data = json.load(read_file)
        if str(dialog_id) not in data:
            return 0
        return data[str(dialog_id)]


async def get_posts(dialog, posts_amount):
    index = 0
    current_grouped_id = None
    posts = []
    post_template = {
        'text': '',
        'photos': [],
        'videos': []
    }
    first = True
    last_id = get_last_msg_id(dialog.id)
    current_last_id = last_id
    async for message in client.iter_messages(dialog):
        print(f'last id: {current_last_id}; message id: {message.id}')
        if message.id > current_last_id:
            current_last_id = message.id

        if last_id >= message.id:
            save_last_id(dialog.id, current_last_id)
            break

        if first or current_grouped_id != message.grouped_id or message.grouped_id is None:
            current_grouped_id = message.grouped_id
            posts.append(copy.deepcopy(post_template))
            if not first:
                index += 1
            first = False

        if index >= posts_amount:
            save_last_id(dialog.id, current_last_id)
            break
        if message.message:
            posts[index]['text'] += message.message
        if message.video:
            continue
            posts[index]['videos'].append(message.video)

        if message.photo:
            posts[index]['photos'].append(message.photo)
    return posts


async def main(client):
    clear_media()
    await client.start()
    # await print_chanels(client)
    channels = await get_channels_dict(client)
    print('Enter index of channel')
    for case in [f'{ch}: {channels[ch]["name"]}' for ch in channels]:
        print(case)
    channel_index = int(input("Enter index: "))
    print(f'Selected channel is: {channels[channel_index]["name"]}')
    # posts_amount = int(input("Enter (number) how many posts download (type `1` if it's background updating): "))
    default_posts_amount = 10
    posts_amount = 10
    dialog = channels[channel_index]['dialog']

    first_iteration = True
    while True:
        posts_amount = default_posts_amount

        if first_iteration:
            first_iteration = False
            posts_amount = 1

        clear_media()
        print('Downloading posts...')
        posts = await get_posts(dialog, posts_amount)
        for i, post in enumerate(posts):
            if not os.path.exists(f'./media/{i}'):
                os.makedirs(f'./media/{i}')
            for img in post['photos']:
                await client.download_media(img, f'./media/{i}')
            for video in post['videos']:
                await client.download_media(video, f'./media/{i}')

        poster = VkPublicPoster(vk_login, vk_password, vk_group_id)
        print('Uploading posts...')
        for i, post in reversed(list(enumerate(posts))):
            if len(post['photos']) == 0 and len(post['text']) == 0:
                continue

            files = os.listdir(f'./media/{i}')
            atachs_ids = []
            for file in files:
                ph_id, ph_owner_id = poster.upload_photo(f'./media/{i}/{file}')
                atachs_ids.append({'ph_id': ph_id, 'ph_owner_id': ph_owner_id})
            attachments = [f'photo{at_id["ph_owner_id"]}_{at_id["ph_id"]}' for at_id in atachs_ids]

            poster.post_post(post['text'], attachments)
            print('Posts published')

        print('Sleep...')
        time.sleep(5)


if __name__ == '__main__':
    print('___Telegram work start___')
    client = TelegramClient(app_name, app_id, app_hash)
    with client:
        client.loop.run_until_complete(main(client))
    print('___Telegram work end___')
