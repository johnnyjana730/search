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

def scrape_google_maps_instance(queries):
    return ScrapeGoogleMaps(queries=queries)


def query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = 200):
    google_info_dic = {}

    all_searches = []
    place_names = load_place_data(place_file_name)
    queries = []
    place2query = {}
    count = 0
    for place_name, note_list in place_names.items():
        print('place_name = ', place_name)
        if len(place_name.replace(' ', '')) < 3 and len(place_name.replace(' ', '')) > 50: continue
        if count_chinese_letters(place_name) > 10: continue
        if count_english_words(place_name) == 1: continue
        search_p_names = [place_name.replace('\n', ''), cur_loc + place_name.replace('\n', '')]
        search_p_names = [p_name for p_name in search_p_names if len(p_name.replace(' ', '')) >= 3]

        for p_name in search_p_names:
            queries.append({"keyword": p_name})
            place2query[p_name] = {'place_name': place_name, 'note_list': note_list}

        count += 1
        if count == 3:
            break
            
    def scrape_google_maps_instance():
        return ScrapeGoogleMaps(queries=queries)

    outputs = launch_tasks(scrape_google_maps_instance)
    print('output = ', outputs)
    input()

        all_candi = []
            # print('search = ', p_name)
            # # 打印搜索结果中的最近地点
            # if places['status'] == 'OK':
            #     nearest_place = places['results'][0]
            #     name = nearest_place['name']
            #     address = nearest_place.get('vicinity', 'N/A')
            #     rating = nearest_place.get('rating', 'N/A')
            #     similarity_ratio = fuzz.partial_ratio(place_name, name)
                
            #     # Get the coordinates (latitude and longitude) of the place
            #     place_coords = (nearest_place['geometry']['location']['lat'], nearest_place['geometry']['location']['lng'])

            #     # Calculate the distance between the place and Los Angeles
            #     distance = great_circle(city_coords, place_coords).miles
            #     if distance <= MAX_DISTANCE and similarity_ratio > 50:  # Set your desired maximum distance
            #         all_candi.append([-similarity_ratio, nearest_place])


    #     if len(all_candi) > 0:
    #         all_candi = sorted(all_candi, key=lambda x: (x[0]))
    #         _, f_candi = all_candi[0] 

    #         print(f"search: {place_name} found: {f_candi['name']} type: {f_candi['types']}")
    #         # input()

    #         flag = False
    #         for p_type in place_type:
    #              if p_type in f_candi['types']:
    #                 flag = True
    #         for p_type in place_type_not:
    #              if p_type in f_candi['types']:
    #                 flag = False

    #         if flag: 
    #             f_candi['note'] = []
    #             for note_id in list(set(note_list)):
    #                 f_candi['note'].append(note_id)

    #             print(f"search: {place_name} found: {f_candi['name']} type: {f_candi['types']}" + f", rate: {f_candi.get('rating', 'N/A')}")
    #             if f_candi['name'] in google_info_dic:
    #                 for note_id in google_info_dic[f_candi['name']]['note']:
    #                     f_candi['note'].append(note_id)

    #             f_candi['note'] = list(set(f_candi['note']))
    #             google_info_dic[f_candi['name']] = f_candi

    # save_data(place_file_name, city_name, google_info_dic)

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

    place_file_name = r"LA 登山"
    place_type      = ['campground', 'tourist_attraction', 'natural_feature', 'locality']
    place_type_not  = ['travel_agency', 'postal_code', 'locality', 'food']
    MAX_DISTANCE = 300

    # los_angeles_coords = (34.0522, -118.2437)
    city_coords = (34.0522, -118.2437)

    query_google_info(place_file_name, city_name, place_type, place_type_not, city_coords, MAX_DISTANCE = MAX_DISTANCE)