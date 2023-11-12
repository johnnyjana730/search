import pickle
import pandas as pd
from utils import *
import argparse
from fuzzywuzzy import fuzz
from geopy.distance import great_circle

# import sys
# # Add a new directory to sys.path
# sys.path.insert(0, 'C://Users//Chang-YuTai//speed2go//data_process//google_map//google_maps_scraper//')

from src.scrape_google_maps import ScrapeGoogleMaps
from src.scrape_google_maps_links_task import ScrapeGoogleMapsLinksTask
from botasaurus.botasaurus.launch_tasks import launch_tasks
from bose import LocalStorage


# Initialize the Google Maps client.
cur_loc = "Los Angeles "


def generate_query(place_names):
    count = 0
    queries = []
    same_place_name = {}
    for place_name, note_list in place_names.items():
        if place_name not in same_place_name:
            same_place_name[place_name] = note_list
        else:
            same_place_name[place_name] += note_list

    for place_name, note_list in same_place_name.items():
        print('place_name = ', place_name)
        if len(place_name.replace(' ', '')) < 3 and len(place_name.replace(' ', '')) > 50: continue
        if count_chinese_letters(place_name) > 10: continue
        if count_english_words(place_name) == 1 and count_chinese_letters(place_name) == 0: continue
        search_p_names = [place_name.replace('\n', ''), cur_loc + place_name.replace('\n', '')]
        search_p_names = [p_name for p_name in search_p_names if len(p_name.replace(' ', '')) >= 3]

        for p_name in search_p_names:
            queries.append({"keyword": p_name, 'extracted_place_name': place_name, 'xhs_note_list': note_list})

        count += 1

    return queries

def run_google_map_scraper(queries):
    def scrape_google_maps_instance():
        return ScrapeGoogleMaps(queries=queries, city = "LA")

    outputs = launch_tasks(scrape_google_maps_instance)
    # print('output = ', outputs)
    # input()

    place_name_result = {}
    for output in outputs:
        place_name = output['extracted_place_name']
        if place_name not in place_name_result:
            place_name_result[place_name] = []
        place_name_result[place_name].append(output)

    return place_name_result

def query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = 200):
    google_info_dic = {}

    place_names = load_place_data(place_file_name)
    queries = generate_query(place_names)
    place_name_result = run_google_map_scraper(queries)

    for place_name, search_results in place_name_result.items(): 
        all_results = []
        for result in search_results:

            # print('search = ', p_name)
            # # 打印搜索结果中的最近地点
            # if places['status'] == 'OK':
            #     nearest_place = places['results'][0]
            name = result['title']
            similarity_ratio = fuzz.partial_ratio(place_name, name)

            # Get the coordinates (latitude and longitude) of the place
            place_coords = result['cordinates']
            # Calculate the distance between the place and Los Angeles
            distance = great_circle(city_coords, place_coords).miles

            if distance <= MAX_DISTANCE and similarity_ratio > 50:  # Set your desired maximum distance
                all_results.append([-similarity_ratio, result])

        if len(all_results) > 0:
            all_results = sorted(all_results, key=lambda x: (x[0]))
            _, result = all_results[0]
            xhs_note_list = result['xhs_note_list']

            print(f"search: {place_name} found: {result['title']} type: {result['main_category']}")
            # input()

            flag = True
            for p_type in place_type:
                if result['categories'] != None and p_type in result['categories']:
                    flag = True
            for p_type in place_type_not:
                if result['categories'] == None or p_type in result['categories']:
                    flag = False

            if flag: 
                result['note'] = []
                for note_id in list(set(xhs_note_list)):
                    result['note'].append(note_id)

                print(f"search: {place_name} found: {result['title']} types: {result['categories']}"
                     + f", rate: {result.get('rating', 'N/A')}")
                if result['title'] in google_info_dic:
                    for note_id in google_info_dic[result['title']]['note']:
                        result['note'].append(note_id)

                result['note'] = list(set(result['note']))
                google_info_dic[result['title']] = result

    save_data(place_file_name, city_name, google_info_dic)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--note_name",
        help="Prompt to generate images for",
        type=str
    )
    parser.add_argument(
        "--city_name",
        help="Prompt to generate images for",
        type=str
    )

    args = parser.parse_args()
    city_name = "LA"
    # place_file_name = 'LA_japfood'
    # place_type      = ['restaurant']
    # place_type_not  = ['shopping_mall',  'grocery_or_supermarket', 'supermarket']

    # place_file_name = 'LA_viewpt'
    # place_type      = ['hindu_temple', 'place_of_worship', 'tourist_attraction',
    #      'natural_feature', 'art_gallery', 'church', 'shopping_mall', 'political', 'colloquial_area']
    # # place_type_not  = ['restaurant', 'park', 'store', 'clothing_store']
    # place_type_not  = ['restaurant', 'store', 'clothing_store']

    # place_file_name = 'LA_hiking'
    # place_type      = ['campground', 'tourist_attraction', 'natural_feature', 'locality']
    # place_type_not  = ['travel_agency', 'postal_code']
    # MAX_DISTANCE = 300

    # place_file_name = r"LA 登山"
    # place_type      = ['campground', 'tourist_attraction', 'natural_feature', 'locality']
    # place_type_not  = ['travel_agency', 'postal_code', 'locality', 'food']
    # MAX_DISTANCE = 300

    place_file_name = r"LA 拍照"
    place_type      = []
    place_type_not  = ['travel_agency', 'postal_code']
    MAX_DISTANCE = 300


    # los_angeles_coords = (34.0522, -118.2437)
    city_coords = (34.0522, -118.2437)

    query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = MAX_DISTANCE)