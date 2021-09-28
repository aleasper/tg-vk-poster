import vk_api


class VkPublicPoster:

    def __init__(self, login, password, group_id):
        self.vk_session = vk_api.VkApi(login, password)
        self.vk_session.auth()
        self.vk = self.vk_session.get_api()
        self.user_id = self.vk.users.get()[0]['id']
        self.group_id = group_id

    def upload_photo(self, photo_path):
        upload = vk_api.VkUpload(self.vk_session)

        # Загрузка изображения на сервер
        photo_res = upload.photo_wall(photos=photo_path, user_id=self.user_id, group_id=self.group_id)

        # Получение id изображения и владельца
        ph_id = photo_res[0]['id']
        ph_owner_id = photo_res[0]['owner_id']

        return ph_id, ph_owner_id
    #
    # def post_img(self, vk_session, ph_id, ph_owner_id):
    #     vk = vk_session.get_api()
    #
    #     # Добавление в пост изображения и публикация
    #     res = vk.wall.post(owner_id=-194490675, from_group=1, attachments=f'photo{ph_owner_id}_{ph_id}')
    #
    def post_post(self, msg, attachments=[]):
        attachments_str = ','.join(attachments)
        res = self.vk.wall.post(owner_id=self.group_id, from_group=1, message=msg, attachments=attachments_str)
        print(res)
