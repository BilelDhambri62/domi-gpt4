"""
This module provides helper functions for interacting with OpenAI's API, including analyzing images.
"""
import os
import base64
import openai
import requests

os.environ["OPENAI_API_KEY"] = "API"
def analyze_multiple_images_with_openai(base64_images):
    """
    Analyzes multiple images using OpenAI's API to extract specific information
    based on a set prompt.
    
    Parameters:
    base64_images (list of str): A list of base64 encoded images to be analyzed.
    Returns:
    dict: The response from OpenAI's API.
    """
    openai.api_key = os.environ["OPENAI_API_KEY"]
    prompt_v6 = """
    I will provide you with a domiciliation document in French and request that you classify and extract recipient information(s) (if available).
    Step 1: Determine if the document includes the recipient's address: '60 RUE FRANCOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France'. If found, extract the information(s) directly preceding the address, which may include the recipient's personal name (e.g., M. REMI LEROY, M. GANTASSI SAMIR, Mme ROHR SEVERINE), the recipient organisation's name (e.g., SCI Au clair de la vue, H2 CARS, Eclipse Holding, SAS 3DS CONSTRUCTION, Serge Aboto, MANZI AND CO, PUUURPLE, FLEXGEN, THOMAS), or both.
Important: Ensure not to overlook any recipient information associated with the address '60 RUE FRANÇOIS 1ER, 75008 PARIS 08' or '60 rue François 1er 75008 Paris France'. Extract recipient information only if the address precisely matches '60 RUE FRANÇOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France'.
Important: Extract only information found within the same field of the recipient address '60 RUE FRANCOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France'.
Important: If the name 'LEGALPLACE' is found alongside the recipient address '60 RUE FRANCOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France', do not extract it as either the recipient's personal name or the recipient organization's name.
Important: The recipient's personal name may be preceded by abbreviations such as "MME", "MR", "Mlle", "M LE REPRESENTANT LEGAL", "Madame"ou "Monsieur" Ensure that when extracting names, these abbreviations are not included.
If the document contains multiple recipients, return a JSON object with 'Publicity' set to 'False' and a list of JSON objects containing the information for each recipient.
Step 2: If the document does not contain the recipient address '60 RUE FRANCOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France', determine whether the document is an advertisement. Respond with 'True' if it is; otherwise, respond with 'False'.
If the document contains only advertisements, return an empty JSON object with 'Publicity' set to 'True' and all other keys (organisme_destinataire, nom_personnel_destinataire, adresse_destinataire) set to ''.
Do not extract any information if the recipient's address in the image does not correspond to '60 RUE FRANCOIS 1ER 75008 PARIS 08' or '60 rue François 1er 75008 Paris France'.
The output should be in JSON format with ('Publicity' and the list (if the document contains different recipient information) with ('organisme_destinataire', 'nom_personnel_destinataire', 'adresse_destinataire')).
The output should always in format JSON correct without any descriptipon:
For exemple :
{
    "Publicity": "",
    "destinataires": [
    {
        "organisme_destinataire": "",
        "nom_personnel_destinataire": "",
        "adresse_destinataire": ""
    }
    ]
},
{
    "Publicity": "",
    "destinataires": []
}

"""
    # Create a list of image messages
    image_messages = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
        for base64_image in base64_images
    ]
    # Construct the payload
    payload = {
        "model": "gpt-4-vision-preview",
        "temperature":0.00000001,
        #"seed":0,
        "top_p":1,
        "frequency_penalty":0,
        "presence_penalty":0, # this is the degree of randomness of the model's output
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_v6
                    },*image_messages  # Add the image messages
                ]
            },

        ],
        "max_tokens": 1000
    }
    # Make the API call
    response = openai.ChatCompletion.create(**payload)
    return response
  

def analyze_image_with_openai(image_path,url):
    """
    Analyzes an image using OpenAI's API to classify and extract recipient information.
    
    Parameters:
    image_path (str): The file path of the image to be analyzed.
    
    Returns:
    dict: The response from OpenAI's API.
    """
    openai.api_key = os.environ["OPENAI_API_KEY"]
    prompt = """
    I will provide you with a domiciliation document in French \
and request its classification and extraction of recipient information. \
First, determine whether the document is an advertising document. \
Respond with 'True' if it is; otherwise, respond with 'False'. \
In general, if the document contains the recipient's address as '60 RUE FRANCOIS 1ER 75008 PARIS',\
then it is not considered an advertising document. Next, extract the recipient's information.\
Before extraction, verify if the document includes the recipient's address: '60 RUE FRANCOIS 1ER 75008 PARIS'. \
If it does, extract the information directly preceding the address (if available), \
which may include the recipient's personal name (For exemple : M. REMI LEROY, M. GANTASSI SAMIR, Mme ROHR SEVERINE, etc),\
the recipient organization's name (For exemple : SCI Au clair de la vue, H2 CARS, Eclipse Holding, SAS 3DS CONSTRUCTION, \
Serge Aboto, MANZI AND CO, PUUURPLE, FLEXGEN, THOMAS, etc), or both, along with their address in JSON format. \
The required fields are: 'Publicity' (Boolean), 'organisme_destinataire' (string), 'nom_personnel_destinataire' (string), \
and 'adresse_destinataire' (string). \
Otherwise, if the document contains only advertisements, \
it should return an empty JSON object with the key 'Publicity' set to true, and all other keys(organisme_destinataire, \
nom_personnel_destinataire, adresse_destinataire) empty.

"""
    if url:
        response = requests.get(image_path, timeout=10)
        if response.status_code == 200:
            base64_images = base64.b64encode(response.content).decode('UTF-8')
        else:
            raise ValueError(f"Failed to fetch image from URL: {image_path}")
    else:
        with open(image_path, 'rb') as image_file:
            base64_images = base64.b64encode(image_file.read()).decode('UTF-8')

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_images}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    # Make the API call
    response = openai.ChatCompletion.create(**payload)
    return response.choices[0].message.content