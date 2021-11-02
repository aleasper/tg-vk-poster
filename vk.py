import logging
from settings import app_id

import vk_api

from ui import auth_vk_handler


class VkPublicPoster:

    def __init__(self, login, password, group_id, logger):
        self.vk_session = vk_api.VkApi(login, password, auth_handler=auth_vk_handler, app_id=app_id, scope='wall, photos')
        self.vk_session.auth()
        self.vk = self.vk_session.get_api()
        self.user_id = self.vk.users.get()[0]['id']
        self.group_id = group_id
        self.logger = logger

    def upload_photo(self, photo_path):
        upload = vk_api.VkUpload(self.vk_session)

        # Загрузка изображения на сервер
        photo_res = upload.photo_wall(photos=photo_path, user_id=self.user_id, group_id=self.group_id)

        # Получение id изображения и владельца
        ph_id = photo_res[0]['id']
        ph_owner_id = photo_res[0]['owner_id']

        return ph_id, ph_owner_id

    def post_post(self, msg, attachments=None):
        if attachments is None:
            attachments = []
        attachments_str = ','.join(attachments)
        res = self.vk.wall.post(owner_id=self.group_id, from_group=1, message=msg, attachments=attachments_str)
        self.logger.debug(res)
        print(res)
        return res
