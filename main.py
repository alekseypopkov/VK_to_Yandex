import requests
import datetime
import json
from tqdm import tqdm

with open('tokens.txt') as file_object:
    TOKEN_VK = file_object.readline().strip()
    TOKEN_YANDEX = file_object.readline().strip()

def find_max_dpi(dict_in_search):
    max_dpi = 0
    need_elem = 0
    for j in range(len(dict_in_search)):
        file_dpi = dict_in_search[j].get('width') * dict_in_search[j].get('height')
        if file_dpi > max_dpi:
            max_dpi = file_dpi
            need_elem = j
    return dict_in_search[need_elem].get('url'), dict_in_search[need_elem].get('type')

def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time

class UserVk:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {'access_token': token, 'v': version}

    def get_photo(self, vk_id: str):
        photos_url = self.url + 'photos.get'
        photos_params = {
            'owner_id': vk_id,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1
        }
        photo_info = requests.get(photos_url, params={**self.params, **photos_params}).json()['response']
        return photo_info['count'], photo_info['items']

    def parsed_photo(self, photo_info: list):
        picture_dict = {}
        json_list = []
        sorted_dict = {}
        counter = 0
        photo_count, photo_items = photo_info
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = find_max_dpi(photo_items[i]['sizes'])
            time_warp = time_convert(photo_items[i]['date'])
            new_value = picture_dict.get(likes_count, [])
            new_value.append({'likes_count': likes_count,
                              'add_name': time_warp, 'url_picture':
                                  url_download, 'size': picture_size})
            picture_dict[likes_count] = new_value
        for elem in picture_dict.keys():
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                else:
                    file_name = f'{value["likes_count"]} {value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                if value["likes_count"] == 0:
                    sorted_dict[file_name] = picture_dict[elem][counter]['url_picture']
                    counter += 1
                else:
                    sorted_dict[file_name] = picture_dict[elem][0]['url_picture']
        return json_list, sorted_dict


class UserYandex:

    def __init__(self, token, num=5):
        self.headers = {'Authorization': token}
        self.added_files_num = num
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"

    def create_folder(self, name_dir: str):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': name_dir}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка {name_dir} успешно создана в корневом каталоге Яндекс диска\n')
        else:
            print(f'\nПапка {name_dir} уже существует. Файлы с одинаковыми именами не будут скопированы\n')
        return name_dir

    def upload_file(self, dict_files: list, name_dir: str):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        copy_counter = 0
        params = {'path': name_dir}
        resource = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        in_folder_list = []
        for elem in resource:
            in_folder_list.append(elem['name'])
        for key, i in zip(dict_files.keys(), tqdm(range(self.added_files_num))):
            if copy_counter < self.added_files_num:
                if key not in in_folder_list:
                    params = {'path': f'{name_dir}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    copy_counter += 1
                else:
                    print(f'Внимание:Файл {key} уже существует')
            else:
                break

        print(f'\nЗапрос завершен, новых файлов скопировано (по умолчанию: 5): {copy_counter}'
              f'\nВсего файлов в исходном альбоме VK: {len(dict_files)}')


def main():
    id_vk = input('Введите id Vk: ')
    user_vk = UserVk(TOKEN_VK, '5.131')
    name_directory = input('Введите название папки: ')
    json_photo = user_vk.get_photo(id_vk)
    parsed_photo = user_vk.parsed_photo(json_photo)
    json_list, export_dict = parsed_photo
    user_yandex = UserYandex(TOKEN_YANDEX)
    user_yandex.create_folder(name_directory)
    user_yandex.upload_file(export_dict, name_directory)  # Загружаем подготовленный словарь с фото на Я.диск
    with open('j_photo.json', 'w') as json_file:  # Сохранение JSON списка в файл json
        json.dump(json_list, json_file)


if __name__ == '__main__':
    main()



