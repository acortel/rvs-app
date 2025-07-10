import requests
import os

def download_image(url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    filename = os.path.basename(url.split('?')[0])
    local_path = os.path.join(dest_folder, filename)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_path
