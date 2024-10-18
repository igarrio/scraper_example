from bs4 import BeautifulSoup
import os
import requests
import pickle
import json
from datetime import datetime
import traceback


def get_div_info(index, source):
    div_elements = source.find_all('div', {'class': 'col-lg-8'})
    if index == 3:
        if index < len(div_elements):
            p_elements = div_elements[index].find_all('p')
            text = ' '.join(p.text for p in p_elements)
        else:
            text = ''
    elif index == 4:
        if index < len(div_elements):
            text = ''
            for child in div_elements[index].children:
                if child.name == 'h3':
                    text += child.text + ': '
                elif child.name == 'div':
                    p_elements = child.find_all('p')
                    for p in p_elements:
                        text += p.text + ' '

    elif index == 5:
        if index < len(div_elements):
            text_element = div_elements[index].find('div', {
                'class': 'text text-lg1 text-normal text-leading-normal text-gray-700 markdown-text'})
            if text_element:
                text = text_element.text
                text = text.replace('\n', '')

    return text


def get_mark_detail(source):
    div_elements = source.find_all('div', {'class': 'long-description'})
    text = ''
    for div in div_elements:
        p_elements = div.find_all('p')
        if p_elements:
            text += ' '.join(p.text for p in p_elements)
    if text:
        return text
    else:
        print('Mark detail 404')
        return ''


def get_mark_location(source, url):
    parent_div = source.find('div', class_='map-data')
    locations = parent_div.find_all('div', class_=['mappable', 'feature-location'])

    coordinates = {}
    for location in locations:
        title = location['data-title']
        lat = location['data-lat']
        lng = location['data-lng']

        mark_id = location['data-id']
        response = requests.get(url + f'/ajaxshow?extend=sites&detail={mark_id}')
        mark_page = BeautifulSoup(response.text, 'html.parser')
        mark_detail = get_mark_detail(mark_page)
        coordinates[title] = {
            'lat & lng': [lat, lng],
            'description': mark_detail,

        }

    return coordinates


def selec_one_txt(source, css_path):
    element = source.select_one(css_path)
    if element:
        return element.text
    else:
        return ""


def writing_json(data):
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output')
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f'output.json')
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    existing_data.append(data)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False)


def main():
    with open('voicemap-urls.pkl', 'rb') as f:
        links = pickle.load(f)
        f.close()

        for url in links:
            try:
                print(url)
                response = requests.get(url)
                response_ajax = requests.get(url + '/ajaxshow')
                head_page = BeautifulSoup(response.text, 'html.parser')
                head_page_ajax = BeautifulSoup(response_ajax.text, 'html.parser')
                duration = selec_one_txt(source=head_page,
                                         css_path='div.d-flex.align-items-center.justify-content-between.text.text-sm.text-medium.text-gray-800 > div:nth-child(3)')
                distance = selec_one_txt(source=head_page,
                                         css_path='div.d-flex.align-items-center.justify-content-between.text.text-sm.text-medium.text-gray-800 > div:nth-child(5)')

                scripts_ld = head_page.find_all('script', type='application/ld+json')
                script_about = scripts_ld[2]
                data = json.loads(script_about.string, strict=False)
                name = data['name']
                description = data['description']

                try:
                    rating = data['aggregateRating']['ratingValue']
                    rating_count = data['aggregateRating']['ratingCount']
                except KeyError as e:
                    rating = ''
                    rating_count = ''

                start_point_info = get_div_info(3, head_page_ajax)
                tips_info = get_div_info(4, head_page_ajax)
                last_update_info = get_div_info(5, head_page_ajax)
                date_object = datetime.strptime(last_update_info, "%d %b %Y")
                last_update_info = date_object.strftime("%Y-%m-%d")
                coordinate = get_mark_location(head_page, url)
                data = {
                    'name': name,
                    'url': url,
                    'details': {
                        'description': description,
                        'rating': rating,
                        'rating count': rating_count,
                        'start point info': start_point_info,
                        'tips': tips_info,
                        'last update': last_update_info,
                        'distance': distance,
                        'duration': duration
                    }
                }
                data['location marks'] = coordinate
                writing_json(data)
                data.clear()
            except Exception as e:
                traceback.print_exc()
                print(f"{url} was not processed")


if __name__ == '__main__':
    main()
