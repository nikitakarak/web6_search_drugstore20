import requests
from io import BytesIO
from decimal import Decimal
from typing import List
from dataclasses import dataclass
from math import radians, cos, sin, sqrt, atan2, ceil


# API Геокодера (поиск топонимических объектов)
# https://tech.yandex.ru/maps/geocoder/doc/desc/concepts/about-docpage/
_GEOCODER_API_SERVER = 'http://geocode-maps.yandex.ru/1.x/'
_GEOCODER_API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'

# Static API для Яндекс.Карт
# https://tech.yandex.ru/maps/staticapi/doc/1.x/dg/concepts/about-docpage/
_MAP_API_SERVER = 'http://static-maps.yandex.ru/1.x/'

# API поиска по организациям
# https://tech.yandex.ru/maps/geosearch/doc/concepts/about-docpage/
_SEARCH_API_SERVER = "https://search-maps.yandex.ru/v1/"
_SEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"  # Ключ на 2019-2020 учебный год


def get_toponym_long_lat(address):
    geocoder_params = {
        'apikey': _GEOCODER_API_KEY,
        'geocode': address,
        'results': 1,
        'format': 'json'
    }

    response = requests.get(_GEOCODER_API_SERVER, params=geocoder_params)
    if not response:
        return ()

    json_response = response.json()
    geo_object = json_response["response"] \
        ["GeoObjectCollection"] \
            ["featureMember"][0] \
                ["GeoObject"]
    return geo_object["Point"]["pos"].split(" ")


def get_toponym_by_long_lat(long_lat, **kwargs):
    geocoder_params = {
        'apikey': _GEOCODER_API_KEY,
        'geocode': ','.join(long_lat),
        'results': 1,
        'format': 'json'
    }
    geocoder_params.update(kwargs)

    response = requests.get(_GEOCODER_API_SERVER, params=geocoder_params)
    if not response:
        return ''

    json_response = response.json()
    return json_response['response'] \
        ['GeoObjectCollection'] \
            ['featureMember'][0] \
                ['GeoObject'] \
                    ['metaDataProperty'] \
                        ['GeocoderMetaData'] \
                            ['text']


def get_toponym_spn(address):
    geocoder_params = {
        'apikey': _GEOCODER_API_KEY,
        'geocode': address,
        'results': 1,
        'format': 'json'
    }

    response = requests.get(_GEOCODER_API_SERVER, params=geocoder_params)
    if not response:
        return ''

    json_response = response.json()
    bbox = json_response['response'] \
        ['GeoObjectCollection'] \
            ['featureMember'][0] \
                ['GeoObject'] \
                    ['boundedBy'] \
                        ['Envelope']

    return ','.join(
        (str(u - l) for u, l in zip(
            (Decimal(s) for s in bbox['upperCorner'].split(' ')),
            (Decimal(s) for s in bbox['lowerCorner'].split(' '))
        ))
    )


@dataclass
class Organization:
    name: str
    address: str
    hours: str
    coords: List[Decimal]


def get_organizations(long_lat, text='', **kwargs):
    search_params = {
        'apikey': _SEARCH_API_KEY,
        'text': text,
        'lang': 'ru_RU',
        'results': 1,
        'll': ','.join(long_lat),
        'type': 'biz'
    }
    search_params.update(kwargs)

    response = requests.get(_SEARCH_API_SERVER, params=search_params)
    if not response:
        return None

    json_response = response.json()
    organizations = []
    for organization in json_response["features"][:search_params['results']]:
        organizations.append(Organization(
            organization["properties"]["CompanyMetaData"]["name"],
            organization["properties"]["CompanyMetaData"]["address"],
            organization["properties"]["CompanyMetaData"]["Hours"]['text'],
            organization["geometry"]["coordinates"]))

    return organizations


# https://tech.yandex.ru/maps/staticapi/doc/1.x/dg/concepts/markers-docpage/
def format_point(long_lat, style):
    return f'{long_lat[0]},{long_lat[1]},{style}'


def format_points(*points):
    return '~'.join(points)


def get_map_image(long_lat=(), **kwargs):
    map_params = {
        "l": "map"
    }

    if long_lat:
        map_params['ll'] = ','.join(long_lat)

    map_params.update(kwargs)

    if not(('ll' in map_params) or ('pt' in map_params)):
        # Не задан центр карты.
        return None

    response = requests.get(_MAP_API_SERVER, params=map_params)
    if not response:
        return None

    return BytesIO(response.content)


_EARTH_RADIUS = 6_372_795


# https://gis-lab.info/qa/great-circles.html
def calculate_distance(long_lat_A, long_lat_B):
    long1 = radians(long_lat_A[0])
    long2 = radians(long_lat_B[0])
    lat1 = radians(long_lat_A[1])
    lat2 = radians(long_lat_B[1])

    cl1 = cos(lat1)
    cl2 = cos(lat2)
    sl1 = sin(lat1)
    sl2 = sin(lat2)
    delta = long2 - long1
    cdelta = cos(delta)
    sdelta = sin(delta)

    y = sqrt(pow(cl2 * sdelta, 2) + pow(cl1 * sl2 - sl1 * cl2 * cdelta, 2))
    x = sl1 * sl2 + cl1 * cl2 * cdelta

    return ceil(atan2(y, x) * _EARTH_RADIUS)
