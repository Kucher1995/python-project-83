from bs4 import BeautifulSoup
import requests


def get_check_result(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''

    description = soup.find(attrs={"name": "description"})
    if description:
        description = description['content']
    else:
        description = ''

    return {'h1': h1,
            'title': title,
            'description': description
            }


def get_response(url):
    try:
        response = requests.get(url, timeout=1)
    except (requests.exceptions.RequestException,
            requests.exceptions.Timeout):
        return None

    if response and response.status_code == 200:
        return response

    return None
