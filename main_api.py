import pickle
import pandas as pd
from utils import *
import argparse
from fuzzywuzzy import fuzz
from geopy.distance import great_circle
import requests
from collections import defaultdict

import pydash
# import sys
# # Add a new directory to sys.path
# sys.path.insert(0, 'C://Users//Chang-YuTai//speed2go//data_process//google_map//google_maps_scraper//')

from src.scrape_google_maps import ScrapeGoogleMaps
from src.scrape_google_maps_links_task import ScrapeGoogleMapsLinksTask
from botasaurus.botasaurus.launch_tasks import launch_tasks
from bose import LocalStorage


# Initialize the Google Maps client.
cur_loc = "Los Angeles "
CITY = "LA"

def generate_query(cur_loc, place_names):
    queries = []
    same_place_name = defaultdict(list)
    for place_name, note_list in place_names.items():
        same_place_name[place_name] += note_list

    for place_name, note_list in same_place_name.items():
        # print('place_name = ', place_name)
        if check_place_name_valid(place_name) == False: continue
        search_p_names = [place_name.replace('\n', ''), cur_loc + place_name.replace('\n', '')]
        search_p_names = [p_name for p_name in search_p_names if len(p_name.replace(' ', '')) >= 3]

        for p_name in search_p_names:
            queries.append({"keyword": p_name, 'extracted_place_name': place_name, 'xhs_note_list': note_list})

    return queries

def run_google_map_scraper(queries):

    outputs, queries = get_saved_result(queries, CITY)
    
    ngrok_url = "http://ba9c-104-154-141-105.ngrok.io"  # Replace with your ngrok URL
    # Define your queries and city
    for i in range(len(queries)):
        if 5 * i < len(queries):
            cur_queries = queries[5* i: 5 * i + 5]
            queries_json = json.dumps(cur_queries)
            response = requests.get(f"{ngrok_url}/api", params={'queries': queries_json, 'city': CITY})

            if response.status_code == 200:
                data_list = response.json()
                print('cur_queries = ', cur_queries)
                print('data_list = ', data_list)
                assert len(cur_queries) == len(data_list)
                for n_i in range(len(data_list)):
                    keyword = cur_queries[n_i]["keyword"]
                    output_file_path = './output/' + CITY + '/' + pydash.kebab_case(keyword) + '.json'
                    cur_data = data_list[n_i]
                    if len(cur_data) == 0:
                        cur_data = {}
                    with open(output_file_path, 'w') as file:
                        json.dump([cur_data], file)

                    outputs.append(cur_data)

    place_name_result = {}
    for output in outputs:
        print('output = ', output)
        place_name = output['extracted_place_name']
        if place_name not in place_name_result:
            place_name_result[place_name] = []
        place_name_result[place_name].append(output)

    return place_name_result

def query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = 200):
    google_info_dic = {}

    place_names = load_place_data(place_file_name)
    queries = generate_query(cur_loc, place_names)
    place_name_result = run_google_map_scraper(queries)

    for place_name, search_results in place_name_result.items(): 
        all_results = []
        for result in search_results:

            name = result['title']
            similarity_ratio = fuzz.partial_ratio(place_name, name)

            # Calculate the distance between the place and Los Angeles
            place_coords = result['cordinates']
            distance = great_circle(city_coords, place_coords).miles

            if 0.5 < distance <= MAX_DISTANCE and similarity_ratio > 50:  # Set your desired maximum distance
                all_results.append([-similarity_ratio, result])

        if len(all_results) > 0:
            all_results = sorted(all_results, key=lambda x: (x[0]))
            _, result = all_results[0]

            print(f"search: {place_name} found: {result['title']} type: {result['main_category']}")

            types = categories_transfer(result['categories'])

            flag = True
            for p_type in place_type:
                if types != None and p_type in types:
                    flag = True
            for p_type in place_type_not:
                if types != None and p_type in types:
                    flag = False

            if flag == False:
                print('result = ', result)
                input()

            if flag: 
                print(f"search: {place_name} found: {result['title']} types: {result['categories']}"
                     + f", rate: {result.get('rating', 'N/A')}")

                n_data = {"place_name" : result['title'], 'geometry':
                         {"location": {"lat": result['cordinates'][0], "lng": result['cordinates'][1]}}, 
                        "rating" : result['rating'], "note" :  list(set(result['xhs_note_list'])), "types": types}


                if n_data['place_name'] in google_info_dic:
                    for note_id in google_info_dic[n_data['place_name']]['note']:
                        n_data['note'].append(note_id)

                n_data['note'] = list(set(n_data['note']))
                google_info_dic[n_data['place_name']] = n_data

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

    place_file_name = r"LA 打卡"
    # place_file_name = r"LA 拍照"
    place_type      = []
    place_type_not  = ['travel_agency', 'postal_code']
    MAX_DISTANCE = 300


    # los_angeles_coords = (34.0522, -118.2437)
    city_coords = (34.0522, -118.2437)

    query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = MAX_DISTANCE)