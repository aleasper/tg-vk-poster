import json
from pathlib import Path
from pprint import pprint
from shutil import rmtree
import os


def clear_media():
    if not os.path.isdir('media'):
        os.makedirs('./media')
    [f.unlink() for f in Path("./media").glob("*") if f.is_file()]
    for path in Path("./media").glob("**/*"):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            rmtree(path)


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

async def save_media(client, posts):
    for i, post in enumerate(posts):
        print('______')
        print('saving media for:')
        pprint(posts)
        if not os.path.exists(f'./media/{post["id"]}'):
            os.makedirs(f'./media/{post["id"]}')
        for img in post['photos']:
            await client.download_media(img, f'./media/{post["id"]}')
        if not post['reply_to']:
            print('not found reply')
            print('______')
            continue
        await save_media(client, [post['reply_to']])
