import requests
import os
from dotenv import load_dotenv
import random

def get_comics_picture_info(picture_id):
    url = f'https://xkcd.com/{picture_id}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()

    return response.json()

def download_comics_picture(picture_id):
    download_url = get_comics_picture_info(picture_id)['img']
    response = requests.get(download_url)
    response.raise_for_status()
    picture_name = f'{picture_id}.png'
    with open(picture_name, 'wb') as image:
        image.write(response.content)
 
def check_vk_api_error(response):
    if 'error' in response:
        raise requests.exceptions.HTTPError(response['error']['error_msg'])

def get_upload_information(group_id, access_token, version):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'access_token': access_token,
        'group_id': group_id,
        'v': version
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_vk_api_error(response.json())
    return response.json()['response']['upload_url']

def upload_comics(picture_id, group_id):
    upload_url = get_upload_information(group_id, access_token, version)
    download_comics_picture(picture_id)
    picture_file = open(f'{picture_id}.png', 'rb')
    files = {'photo': picture_file}
    response = requests.post(upload_url, files=files)
    response.raise_for_status()
    response_data = response.json()
    picture_file.close()
    check_vk_api_error(response_data)
    
    return response_data['server'], response_data['photo'], response_data['hash']

def get_post_information(picture_id, group_id, access_token, version):
    server, photo, _hash = upload_comics(picture_id, group_id)
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
       'access_token': access_token,
       'group_id': group_id,
       'v': version,
       'server': server,
       'photo': photo, 
       'hash': _hash
    }
    response = requests.post(url, params=params).json()
    check_vk_api_error(response)

    return response['response'][0]['id'], response['response'][0]['owner_id']

def post_picture(picture_id, group_id, access_token, version):
    media_id, owner_id = get_post_information(picture_id, group_id, access_token, version)
    url = 'https://api.vk.com/method/wall.post'
    params = {
        'access_token': access_token,
        'v': version,
        'owner_id': f'-{group_id}',
        'message': get_comics_picture_info(picture_id)['alt'],
        'attachments': f'photo{owner_id}_{media_id}',
        'from_group': 1,
    }
    
    response = requests.get(url, params=params).json()
    check_vk_api_error(response)

    os.remove(f'{picture_id}.png')

def get_last_comics_number():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()

    return response.json()['num']

if __name__ == "__main__":
    load_dotenv()
    access_token = os.getenv('ACCESS_TOKEN')
    version = 5.103
    group_id = os.getenv('GROUP_ID')
    random_comics = random.randint(1, get_last_comics_number())
    try:
        post_picture(random_comics, group_id, access_token, version)
    except Exception as e:
        print(f'Ошибка: {e}')
    finally:
        os.remove(f'{random_comics}.png')
