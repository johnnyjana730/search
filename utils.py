import json
import csv
import re
import pandas as pd
import os
import pickle
import pathlib
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
