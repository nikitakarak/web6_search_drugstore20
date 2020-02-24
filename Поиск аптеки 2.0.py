from yandex_maps import (
    get_toponym_long_lat, get_organizations,
    format_point, format_points,
    get_map_image
)


if __name__ == '__main__':
    import sys
    from PIL import Image
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        'address',
        help='Исходный адрес. Например: Москва, ул. Ак. Королева, 12')
    # args = parser.parse_args(['Москва, ул. Ак. Королева, 12'])
    args = parser.parse_args()

    long_lat = get_toponym_long_lat(args.address)
    if not long_lat:
        print(f'Не удалось найти координаты для указанного адреса.')
        sys.exit(1)

    organizations = get_organizations(long_lat, 'аптека')
    if not organizations:
        print(f'Не удалось найти предприятие с типом "аптека".')
        sys.exit(2)

    organization = organizations[0]
    print('Адрес:', organization.address)
    print('Название:', organization.name)
    print('Врем работы:', organization.hours)

    Image.open(
        get_map_image(
            pt=format_points(
                format_point(long_lat, r'pm2al'),
                format_point(organization.coords, r'pm2bl')
            )
        )
    ).show()
