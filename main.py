import asyncio
import time
from pprint import pprint
from pathlib import Path
from shutil import rmtree
import copy
import logging

import json

import os

from creds import app_id, app_hash, app_name
from settings import vk_group_id, delay

from telethon.sync import TelegramClient

from ui import get_vk_creds
from vk import VkPublicPoster


stop_patterns = ['https://t.me', '@']




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
        'videos': [],
        'skip': False
    }
    first = True
    last_id = get_last_msg_id(dialog.id)
    current_last_id = last_id
    async for message in client.iter_messages(dialog):
        print('____')
        print(message)
        print(message.get_entities_text())
        for entity, text in message.get_entities_text():
            print(entity, text)
        print('____')
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
            posts[index]['skip'] = True
        if message.photo:
            posts[index]['photos'].append(message.photo)
        if message.reply_to or message.fwd_from:
            posts[index]['skip'] = True


    return posts


def not_valid_text(text):
    for s_p in stop_patterns:
        if s_p in text:
            return True
    return False




async def main(client):
    clear_media()
    await client.start()
    logger.debug('Tg client accepted')
    # await print_chanels(client)
    channels = await get_channels_dict(client)
    logger.debug(f'Channels got: {channels}')
    print('Enter index of channel')
    for case in [f'{ch}: {channels[ch]["name"]}' for ch in channels]:
        print(case)
    channel_index = int(input("Enter index: "))
    print(f'Selected channel is: {channels[channel_index]["name"]}')
    logger.debug(f'Selected channel is: {channels[channel_index]["name"]}')
    default_posts_amount = 10
    posts_amount = 10
    dialog = channels[channel_index]['dialog']
    print('Checking Vk creds')
    vk_login, vk_password = get_vk_creds()
    poster = VkPublicPoster(vk_login, vk_password, vk_group_id, logger)
    logger.debug('Vk client accepted')
    first_iteration = True
    while True:
        logger.debug('Start iteration')
        try:
            posts_amount = default_posts_amount

            if first_iteration:
                first_iteration = False
                posts_amount = 1
            logger.debug(f'Post amount: {posts_amount}')
            clear_media()
            print('Downloading posts...')
            posts = await get_posts(dialog, posts_amount)
            for i, post in enumerate(posts):
                if not os.path.exists(f'./media/{i}'):
                    os.makedirs(f'./media/{i}')
                for img in post['photos']:
                    await client.download_media(img, f'./media/{i}')
                for video in post['videos']:
                    continue
                    # await client.download_media(video, f'./media/{i}')
            logger.debug('Posts downloads')
            print('Uploading posts...')
            for i, post in reversed(list(enumerate(posts))):
                print(post)
                if len(post['photos']) == 0 and len(post['text']) == 0 or\
                        len(post['videos']) != 0 or\
                        not_valid_text(post['text']) or\
                        post['skip']:
                    continue

                files = os.listdir(f'./media/{i}')
                atachs_ids = []
                for file in files:
                    ph_id, ph_owner_id = poster.upload_photo(f'./media/{i}/{file}')
                    atachs_ids.append({'ph_id': ph_id, 'ph_owner_id': ph_owner_id})
                attachments = [f'photo{at_id["ph_owner_id"]}_{at_id["ph_id"]}' for at_id in atachs_ids]

                res = poster.post_post(post['text'], attachments)
                print(f'Post published: {res}')
                logger.debug(f'Post published: {res}')
            logger.debug('Posts published')
            print('Sleep...')
        except Exception as ex:
            print(ex)
            logger.error(ex)

        finally:
            logger.debug('End iteration')
            time.sleep(delay)


if __name__ == '__main__':
    logger = get_logger()
    logger.debug('App started')
    print('Telegram creds check')
    client = TelegramClient(app_name, app_id, app_hash)
    with client:
        client.loop.run_until_complete(main(client))


