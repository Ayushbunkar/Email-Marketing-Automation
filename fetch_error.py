import urllib.request
from urllib.error import HTTPError

try:
    urllib.request.urlopen('http://127.0.0.1:8000/analytics/summary')
except HTTPError as e:
    print(e.read().decode('utf-8'))
