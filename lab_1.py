import json
import requests
import time
from tqdm import tqdm


class Photo:

    def __init__(self, vk_id, ya_disk_token):
        self.vk_token = "958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008"
        self.ya_disk_token = ya_disk_token
        self.id = vk_id

    def get_headers(self):
        return {"Content-Type": "application/json",
                "Authorization": f"OAuth {self.ya_disk_token}"}

    def get_number_id(self):
        number = requests.get("https://api.vk.com/method/users.get", params={"access_token": self.vk_token,
                                                                             "v": "5.131", "user_ids": f"{self.id}"})
        return number.json()['response'][0]['id']

    def get_photo_from_vk(self):
        photos_dict = {}
        resp = requests.get("https://api.vk.com/method/photos.get", params={"access_token": self.vk_token,
                                                                            "owner_id": self.get_number_id(),
                                                                            "v": "5.131", "album_id": "profile",
                                                                            "extended": "1"})
        for item in resp.json()["response"]["items"]:
            if str(item['likes']['count']) in photos_dict:
                name = str(item['likes']['count']) + '_' + str(item['date'])
                photos_dict[name] = [item["sizes"][-1]['url']]
                photos_dict[name].append(item['sizes'][-1]['type'])
            else:
                name = str(item['likes']['count'])
                photos_dict[name] = [item["sizes"][-1]['url']]
                photos_dict[name].append(item['sizes'][-1]['type'])
        return photos_dict

    def get_url_to_upload(self):
        url = requests.get('https://cloud-api.yandex.net:443/v1/disk/resources/upload',
                           headers=self.get_headers(),
                           params={"path": f"/photo from VK/", "overwrite": "True"}).json()['href']
        return url

    def upload_to_yadisk(self):
        # Проверяем есть ли папка с нужным имененем на Диске. Если нет то создаем ее.
        if requests.get('https://cloud-api.yandex.net:443/v1/disk/resources', headers=self.get_headers(),
                        params={'path': '/photo from VK'}).status_code == 404:
            requests.put('https://cloud-api.yandex.net:443/v1/disk/resources', headers=self.get_headers(),
                         params={'path': '/photo from VK'})

        # Загрузка фотографий и создание списка для json-файла
        json_list = []
        files = self.get_photo_from_vk()
        for file_name, file_inside in tqdm(files.items()):
            information = {}
            requests.post('https://cloud-api.yandex.net:443/v1/disk/resources/upload', headers=self.get_headers(),
                          params={'path': f"/photo from VK/{file_name}.jpg", 'url': f"{file_inside[0]}"}).json()
            information["file_name"] = f'{file_name}.jpg'
            information['size'] = file_inside[1]
            json_list.append(information)
            time.sleep(0.5)

        # Записываем в json-файл
        with open('photo_json.json', 'w', encoding='utf-8') as f:
            json.dump(json_list, f, indent=2)
