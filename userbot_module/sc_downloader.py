import requests
from config import SOUNDCLOUD_CLIENT_ID

def search_track(query):
    url = "https://api.soundcloud.com/tracks"
    params = {"q": query, "client_id": SOUNDCLOUD_CLIENT_ID}
    try:
        data = requests.get(url, params=params).json()
        return data[0] if data else None
    except:
        return None


def download_track(track):
    if not track.get("downloadable"):
        return None

    url = track["download_url"] + f"?client_id={SOUNDCLOUD_CLIENT_ID}"
    try:
        content = requests.get(url).content
        filename = track["title"] + ".mp3"
        with open(filename, "wb") as f:
            f.write(content)
        return filename
    except:
        return None
