import requests

def get_random_image():
    """Fetch a random image from Picsum"""
    response = requests.get("https://picsum.photos/200/300")
    if response.status_code == 200:
        return response.url
    else:
        return None

def get_image_by_grayscale():
    """Fetch a random grayscale image from Picsum"""
    response = requests.get("https://picsum.photos/200/300?grayscale")
    if response.status_code == 200:
        return response.url
    else:
        return None