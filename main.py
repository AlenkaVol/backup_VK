import requests
import json
from tqdm import tqdm
from time import sleep
from urllib.parse import urlencode

app_ID = '51720734'


def create_url_token_VK(app_id):
    """Создания ссылки для получения токена ВК"""
    base_url = "https://oauth.vk.com/authorize"
    params = {
        'client_id': app_id,
        'redirect_uri': 'https://oauth.vk.com/blank.html',
        'display': 'page',
        'scope': 'photos',
        'response_type': 'token'
    }

    oauth_url = f'{base_url}?{urlencode(params)}'
    return oauth_url

# получаем токен ВК, перейдя по сформированной ссылке в браузере
# print(create_url_token_VK(app_ID))


token_VK = '...'
token_Ydisk = '...'
userVK_id = '...'


class VKAPIClient:
    API_BASE_URL_VK = 'https://api.vk.com/method'

    def __init__(self, token_vk, user_id, token_yandex_disk):
        self.tokenVK = token_vk
        self.user_id = user_id
        self.tokenYandex = token_yandex_disk

    def _get_common_params(self):
        return {
            'access_token': self.tokenVK,
            'v': '5.131'
        }

    def _build_url(self, api_method):
        return f'{self.API_BASE_URL_VK}/{api_method}'

    def get_profile_photos(self):
        params = self._get_common_params()
        params.update({'owner_id': self.user_id, 'album_id': 'profile', 'extended': 1})
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()

    def folder_creation_ydisk(self, name_folder):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {"path": name_folder}
        headers = {"Authorization": "OAuth " + self.tokenYandex}
        response = requests.put(url, headers=headers, params=params)
        if 200 <= response.status_code < 300:
            print(f'Папка {name_folder} создана')
        else:
            print('Произошла ошибка при создании папки')

    def get_list_all_photos(self):
        info_photos = self.get_profile_photos()
        items = info_photos['response']['items']
        dict_name_check = {}
        for item in items:
            likes = item['likes']['count']
            if likes in dict_name_check.keys():
                dict_name_check[likes] += 1
            else:
                dict_name_check[likes] = 1

        list_all_photos = []
        for item in items:
            dict_photo = {}
            likes = item['likes']['count']
            count = dict_name_check[likes]
            if count > 1:
                date = item['date']
                name_photo = f'{likes}_{date}.jpg'
            else:
                name_photo = f'{likes}.jpg'

            dict_sizes_photo = {}
            sizes = item['sizes']
            for size in sizes:
                height = size['height']
                width = size['width']
                count_size = height*width
                type_size = size['type']
                dict_sizes_photo[type_size] = count_size
                sorted_dict_sizes_photo = {}
                sorted_sizes_photo_keys = sorted(dict_sizes_photo, key=dict_sizes_photo.get, reverse=True)
                for key in sorted_sizes_photo_keys:
                    sorted_dict_sizes_photo[key] = dict_sizes_photo[key]
            biggest_size = list(sorted_dict_sizes_photo.items())[0][0]
            for size in sizes:
                type_size = size['type']
                if type_size == biggest_size:
                    url_photo = size['url']

            dict_photo["file_name"] = name_photo
            dict_photo["size"] = biggest_size
            dict_photo["url"] = url_photo
            list_all_photos.append(dict_photo)

        return list_all_photos

    def save_photos_ydisk(self):
        self.folder_creation_ydisk('profile_photos_vk')
        all_photos = self.get_list_all_photos()
        json_file = []
        for photo in tqdm(all_photos, ncols=100, ascii=False, desc='Total'):
            sleep(0.1)
            json_dict = {}
            name = photo['file_name']
            url_photo = photo['url']
            size_photo = photo['size']
            json_dict['file_name'] = name
            json_dict['size'] = size_photo
            json_file.append(json_dict)
            url_ydisk = "https://cloud-api.yandex.net/v1/disk/resources/upload"
            params = {"path": f'profile_photos_vk/{name}', 'url': url_photo}
            headers = {"Authorization": "OAuth " + self.tokenYandex, 'Accept': 'application/json',
                       'Content-Type': 'application/json'}
            response_1 = requests.get(url_ydisk, headers=headers, params=params)
            if 200 <= response_1.status_code < 300:
                requests.post(url_ydisk, headers=headers, params=params)

        with open('file_info.json', 'w') as f:
            json.dump(json_file, f, indent=2)

        print('Загрузка фото завершена')


if __name__ == '__main__':
    vk_client = VKAPIClient(token_VK, userVK_id, token_Ydisk)
    vk_client.save_photos_ydisk()

