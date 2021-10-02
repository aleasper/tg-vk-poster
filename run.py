import os
from pprint import pprint

from logger import get_logger
from os_work import clear_media, get_last_msg_id, save_media
from tg import Tg
from creds import app_id, app_hash, app_name
from settings import vk_group_id, delay
from ui import get_vk_creds, get_user_channel_select
from vk import VkPublicPoster
import time

import re

stop_regexes = [r'@', r'(http|ftp|https)']


def is_acceptable_post(post):
    if post['skip'] or len(post['photos']) == 0 and len(post['text']) == 0:
        return False

    for stop_regex in stop_regexes:
        if re.match(stop_regex, post['text']) is not None:
            return False
    if not post['reply_to']:
        return True

    return is_acceptable_post(post['reply_to'])


def create_vk_post(vk_client, post, attachments=None, text=None):
    if attachments is None:
        attachments = []
    if text is None:
        text = post['text']
    else:
        text = post['text'] + '\n↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓\n' + text

    files = os.listdir(f'./media/{post["id"]}')
    atachs_ids = []
    for file in files:
        ph_id, ph_owner_id = vk_client.upload_photo(f'./media/{post["id"]}/{file}')
        atachs_ids.append({'ph_id': ph_id, 'ph_owner_id': ph_owner_id})
    attachments = [*attachments, *[f'photo{at_id["ph_owner_id"]}_{at_id["ph_id"]}' for at_id in atachs_ids]]
    if not post['reply_to']:
        return text, attachments
    else:
        return create_vk_post(vk_client, post['reply_to'], attachments, text)


async def main(tg_wrapper, vk_client, logger):
    clear_media()
    await tg.start()
    channels = await tg_wrapper.get_channels_names_dict()
    selected_channel = get_user_channel_select(channels)
    logger.debug(f'Selected channel is: {selected_channel["name"]}')
    dialog = selected_channel['dialog']
    tg_client = tg_wrapper.get_client()
    default_posts_amount = 10
    first_iteration = False
    while True:
        print('___________________')
        print('Start new iteration')
        logger.debug('Main loop started')
        try:
            posts_amount = default_posts_amount
            if first_iteration:
                first_iteration = False
                posts_amount = 1
            print('Downloading posts...')
            last_msg_id = get_last_msg_id(dialog.id)
            posts = await tg.get_posts(dialog, posts_amount, last_msg_id)
            pprint(posts)

            await save_media(tg_client, posts)

            print('Uploading posts...')
            for i, post in reversed(list(enumerate(posts))):
                print(post)
                if not is_acceptable_post(post):
                    continue
                text, attachments = create_vk_post(vk_client, post)
                print('____')
                print('post:')
                print(text)
                print(attachments)
                print('____')
                res = vk_client.post_post(text, attachments)
                print(f'Post published: {res}')
                logger.debug(f'Post published: {res}')
            logger.debug('Posts published')
            print('Sleep...')
        except Exception as ex:
            print(ex)
            logger.error(ex)

        finally:
            logger.debug('End iteration')
            print(f'Sleeping {delay} seconds')
            time.sleep(delay)


if __name__ == '__main__':
    logger = get_logger()
    logger.debug('App started')

    try:
        tg = Tg(app_name, app_id, app_hash, logger)
        print('Tg authentication...')
        tg_client = tg.get_client()
        with tg_client:
            print('Vk authentication...')
            vk_login, vk_password = get_vk_creds()
            vk_client = VkPublicPoster(vk_login, vk_password, vk_group_id, logger=logger)
            tg_client.loop.run_until_complete(main(tg, vk_client, logger))

    except Exception as ex:
        print(ex)
        logger.error(ex, ex.args, ex.__str__())
