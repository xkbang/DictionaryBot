
import requests
from bs4 import BeautifulSoup
import re
import os
from int3106.image_tools import download_images

# Existing functions --------------------------------------

def dictionary(word):
    url = 'https://dictionary.cambridge.org/dictionary/english-chinese-traditional/' + word
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"
    headers = {'User-Agent': user_agent}

    # Make the web request
    web_request = requests.get(url, headers=headers)
    soup = BeautifulSoup(web_request.text, "html.parser")

    word_dict = {}
    headword_list = []

    # Check if 'di-body' is present
    di_body = soup.find('div', {'class': 'di-body'})
    if di_body is not None:
        # Get Headword
        headword = di_body.find('span', {'class': 'hw dhw'})
        if headword:
            headword_list.append(headword.get_text(strip=True))

    if not headword_list:
        # No valid entry found
        return {}

    # Initialize the word_dict with headwords
    for w in headword_list:
        word_dict[w] = {'parts_of_speech': []}

    # Extract parts of speech, definitions, translations, and examples
    for entry in di_body.find_all('div', class_='entry-body__el'):
        pos_elem = entry.find('span', {'class': 'pos dpos'})
        if not pos_elem:
            # If no part of speech is found, skip
            continue
        pos = pos_elem.get_text(strip=True)
        usage = entry.find('span', {'class': 'usage dusage'})
        usage = usage.get_text(strip=True) if usage else ""

        definitions = []
        pos_body = entry.find('div', class_='pos-body')

        for sense in pos_body.find_all('div', class_='sense-body'):
            definition_elem = sense.find('div', {'class': 'def ddef_d db'})
            if definition_elem:
                definition = definition_elem.get_text().strip()
            else:
                definition = ""

            translation_elem = sense.find('span', {'class': 'trans dtrans dtrans-se break-cj'})
            translation = translation_elem.get_text().strip() if translation_elem else "No translation available"

            examples = []
            for example in sense.find_all('div', class_='examp dexamp'):
                example_text_elem = example.find('span', class_='eg deg')
                if example_text_elem:
                    example_text = example_text_elem.get_text().strip()
                else:
                    example_text = ""
                example_translation = example.find('span', class_='trans dtrans dtrans-se hdb break-cj')
                example_translation_text = example_translation.get_text().strip() if example_translation else ""
                examples.append({
                    'example': example_text,
                    'translation': example_translation_text,
                })

            definitions.append({
                'definition': definition,
                'translation': translation,
                'examples': examples
            })

        # Append the part of speech, usage, and definitions to the dictionary
        word_dict[headword_list[0]]['parts_of_speech'].append({
            'part_of_speech': pos,
            'usage': usage,
            'definitions': definitions
        })

    return word_dict

def format_word_info(word_dict):
    output = []
    for word, details in word_dict.items():
        output.append(f"Word: {word}\n")
        for pos_info in details['parts_of_speech']:
            output.append(f"Part of Speech: {pos_info['part_of_speech']}")
            if pos_info['usage']:
                output.append(f"Usage: {pos_info['usage']}")
            output.append("")
            for definition in pos_info['definitions']:
                output.append(f"Definition: {definition['definition']}")
                output.append(f"Translation: {definition['translation']}\n")
                if definition['examples']:
                    output.append("Examples:")
                    for example in definition['examples']:
                        output.append(f" - Example: {example['example']}")
                        if example['translation']:
                            output.append(f"   Translation: {example['translation']}")
                    output.append("")
    return "\n".join(output)

def get_images(searchKey):
    # This function downloads images and returns local file paths
    # Modify download_images to actually download and store images locally if it doesn't already.
    image_urls = download_images(searchKey)
    image_paths = []
    # Assuming download_images returns URLs, you need a local download or direct usage
    # If the function already downloads, return the local paths.
    # For demonstration, let's assume it downloads into a known directory.
    # You will need to adjust this according to your actual implementation.
    # 
    # If download_images returns a list of local paths, just set image_paths = image_urls directly.
    # Otherwise, you'll need code here to download and save images locally.
    
    # For now, we assume image_urls are direct image URLs and we download them:
    for i, url in enumerate(image_urls[:3]):  # limit to first 3 images
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                filename = f"temp_image_{searchKey}_{i}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                image_paths.append(filename)
        except:
            pass
    
    return image_paths