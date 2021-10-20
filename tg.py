import copy

from telethon import TelegramClient
from telethon.tl.types import MessageEntityTextUrl, MessageMediaPoll

from os_work import save_last_id


class Tg:

    def __init__(self, app_name, app_id, app_hash, logger):
        self.client = TelegramClient(app_name, app_id, app_hash)
        self.logger = logger

    def get_client(self):
        return self.client

    async def start(self):
        await self.client.start()

    async def get_channels_names_dict(self):
        channels = {}
        i = 1
        async for dialog in self.client.iter_dialogs():
            if not dialog.is_group and dialog.is_channel:
                channels[i] = {
                    'name': dialog.name,
                    'dialog': dialog
                }
                i += 1
        return channels

    def save_last_id(self, dialog_id, current_last_id):
        save_last_id(dialog_id, current_last_id)

    async def get_post_from_msg(self, message):

        print(message)

        post = copy.deepcopy({'id': message.id, 'text': '', 'photos': [], 'videos': [], 'skip': False, 'reply_to': {}})
        for entity, text in message.get_entities_text():
            if isinstance(entity, MessageEntityTextUrl) or isinstance(entity, MessageMediaPoll):
                post['skip'] = True
                return post

        if message.video or message.fwd_from or message.reply_markup:
            post['skip'] = True
            return post
        if message.message:
            post['text'] += message.message
        if message.photo:
            post['photos'].append(message.photo)
        if message.reply_to_msg_id:
            post['reply_to'] = await self.get_post_from_msg(await message.get_reply_message())
        return post

    async def get_posts(self, dialog, posts_amount, last_id):
        index = 0
        current_grouped_id = None
        posts = []
        post_template = {
            'id': None,
            'text': '',
            'photos': [],
            'videos': [],
            'skip': False,
            'reply_to': {}
        }
        first = True
        current_last_id = last_id
        async for message in self.client.iter_messages(dialog):
            print(message)
            if message.id > current_last_id:
                current_last_id = message.id

            if last_id >= message.id:
                self.save_last_id(dialog.id, current_last_id)
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

            post = await self.get_post_from_msg(message)
            posts[index]['id'] = post['id']
            posts[index]['text'] = posts[index]['text']+post['text']
            posts[index]['photos'] = [*posts[index]['photos'], *post['photos']]
            posts[index]['reply_to'] = dict(posts[index]['reply_to'], **post['reply_to'])

        return posts
