import asyncio
import time
from pprint import pprint
from pathlib import Path
from shutil import rmtree
import copy

import os

from creds import app_id, app_hash, app_name, vk_login, vk_password, vk_group_id
from telethon.sync import TelegramClient

from vk import VkPublicPoster


def clear_media():
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
    async for message in client.iter_messages(dialog):
        if first or current_grouped_id != message.grouped_id or message.grouped_id is None:
            current_grouped_id = message.grouped_id
            posts.append(copy.deepcopy(post_template))
            if not first:
                index += 1
            first = False

        if index >= posts_amount:
            break

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
    posts_amount = int(input("Enter how many posts download (number): "))
    dialog = channels[channel_index]['dialog']
    posts = await get_posts(dialog, posts_amount)
    pprint(posts)
    for i, post in enumerate(posts):
        if not os.path.exists(f'./media/{i}'):
            os.makedirs(f'./media/{i}')
        for img in post['photos']:
            await client.download_media(img, f'./media/{i}')
        for video in post['videos']:
            await client.download_media(video, f'./media/{i}')

    poster = VkPublicPoster(vk_login, vk_password, vk_group_id)
    for i, post in enumerate(posts):
        if len(post['photos']) == 0 and len(post['text']) == 0:
            continue

        files = os.listdir(f'./media/{i}')
        atachs_ids = []
        for file in files:
            print(file)
            ph_id, ph_owner_id = poster.upload_photo(f'./media/{i}/{file}')
            atachs_ids.append({'ph_id': ph_id, 'ph_owner_id': ph_owner_id})
        attachments = [f'photo{at_id["ph_owner_id"]}_{at_id["ph_id"]}' for at_id in atachs_ids]

        print(post['text'])
        pprint(attachments)

        poster.post_post(post['text'], attachments)


if __name__ == '__main__':
    print('___Telegram work start___')
    client = TelegramClient(app_name, app_id, app_hash)
    with client:
        client.loop.run_until_complete(main(client))
    print('___Telegram work end___')
