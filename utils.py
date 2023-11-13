import json
import csv
import re
import pandas as pd
import os
import pickle
import pathlib
import pydash
import nltk
# nltk.download('punkt')  # Download the Punkt tokenizer models

def load_place_data(file_name):
    place_names = {}
    file_path = f"../../../data/LLM_extract/{file_name}.pickle"
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            place_names = pickle.load(file)

    return place_names

def save_data(file_name, city_name, data_dic):
    # Use pickle.dump to save the dictionary to the file
    pathlib.Path(f'../../../data/Google_map/{city_name}/' ).mkdir(parents=True, exist_ok=True)
    with open(f'../../../data/Google_map/{city_name}/{file_name}.json', "w") as json_file:
        json.dump(data_dic, json_file)

def count_chinese_letters(input_string):
    chinese_count = 0
    for char in input_string:
        # Check if the character is a Chinese character
        if '\u4e00' <= char <= '\u9fff':
            chinese_count += 1
    return chinese_count

def count_english_words(input_text):
    words = nltk.word_tokenize(input_text)
    english_words = [word for word in words if word.isalpha()]  # Filter out non-alphabetic words
    return len(english_words)

def get_saved_result(queries, city):
    outputs = []
    n_queries = []
    for query in queries:
        # print('keyword = ', current_data['keyword'])
        output_file_path = './output/' + city + '/' + pydash.kebab_case(query['keyword']) + '.json'
        print('keyword = ', query['keyword'])
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as file:
                current_output = json.load(file)

            print('current_output = ', current_output)
            if len(current_output) > 0 and len(current_output[0]) > 1 and 'title' in current_output[0]:
                current_output[0]['extracted_place_name'] = query['extracted_place_name']
                current_output[0]['xhs_note_list'] = query['xhs_note_list']
                outputs.append(current_output[0])
        else:
            n_queries.append(query)

    return outputs, n_queries

def check_place_name_valid(place_name):
    if len(place_name.replace(' ', '')) < 3 and len(place_name.replace(' ', '')) > 50: return False
    if count_chinese_letters(place_name) > 10: return False
    if count_english_words(place_name) == 1 and count_chinese_letters(place_name) == 0: return False

    return True
