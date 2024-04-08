"""
This module provides functionalities for processing PDF files. It includes converting images
within PDFs to base64 strings, formatting JSON strings, and analyzing PDF images using OpenAI's
image analysis. It also includes a function to verify recipient information in a given 
analysis result.
"""
import base64
import time 
import io
from io import BytesIO
import json 
import requests
import fitz
from PIL import Image
from fuzzywuzzy import fuzz
from openai_helpers import analyze_multiple_images_with_openai

def images_to_base64(pdf_bytes):
    """
    Converts all images in a PDF file to base64 encoded strings.

    Parameters:
    pdf_path (str): The file path of the PDF.

    Returns:
    list: A list of base64 encoded strings for each image found in the PDF.
    int: The number of images found in the PDF.
    """
    # with open(pdf_path, "rb") as f:
    #     pdf_bytes = f.read()
    #images = pdf2image.convert_from_bytes(pdf_bytes, dpi=300)  # default dpi=200
    # Record the start time
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    try:
        # Use list comprehensions for faster execution
        images = [
            Image.open(io.BytesIO(doc.extract_image(img[0])["image"]))
            for page in range(len(doc))
            for img in doc.get_page_images(page)
        ]
        #images = [img.resize((1920, 1920)) for img in images]
    finally:
        doc.close()
    base64_images = []
    print("Images size:")
    for image in images:
        print(image.size)
        buffered = BytesIO()
        image.save(buffered, format="JPEG")  # Assuming JPEG format
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_images.append(encoded_image)
    return base64_images,len(images)


def format_json_string(s):
    """
    Extracts the JSON string from a larger string, formats it, and returns the JSON object.
    """
    # Finding the start and end of the JSON object
    start = s.find('{')
    end = s.rfind('}') + 1
    # Extracting and formatting the JSON string
    json_str = s[start:end]
    # Converting the string to a JSON object
    try:
        json_obj = json.loads(json_str)
        return json_obj
    except json.JSONDecodeError:
        return "Invalid JSON format"

def analyze_pdf_images(url: str):
    """
    Analyzes images within a PDF file using OpenAI's image analysis.

    Parameters:
    pdf_file_path (str): The file path of the PDF to analyze.

    Returns:s
    tuple: A tuple containing the analysis result message, total tokens used in the analysis,
    and the number of images analyzed.
    """
    try:
        # 1--- GET PDF & Convert to Images
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        pdf_bytes = response.content
        base64_images, nbr_images = images_to_base64(pdf_bytes)
        end_time = time.time()
        processing_time_image = end_time - start_time
        print(f"Processing time images_to_base64: {processing_time_image} seconds")

        start_time = time.time()
        result = analyze_multiple_images_with_openai(base64_images)
        end_time = time.time()  # Record the end time
        processing_time_openai = end_time - start_time 
        print(f"Processing time openAI: {processing_time_openai} seconds")

        return result.choices[0].message.content,result.usage.total_tokens,nbr_images,processing_time_image,processing_time_openai
    except requests.exceptions.RequestException as e:
        print({"error": str(e)})
        return({"error": str(e)})
    except Exception as e:  # Catching any other exceptions
        # Log the error or return a generic error response
        print(f"An unexpected error occurred: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}   

def verifify_recipents_json(analysis_result):
    """
    Verifies recipient information in the analysis result JSON.

    Parameters:
    analysis_result (str): The JSON string containing analysis results.

    Returns:
    dict: A dictionary containing information about the verification results.
    """
    match = {
        "Publicity": False,
        "Valid_recipients": False,
        "unique_recipient":None,
        "Recipients":None,
        "First_recipient":None,
        }
    print(analysis_result)
    # Attempt to load JSON
    try:
        # analysis_result = analysis_result.strip()[8:-3]
        analysis_result=format_json_string(analysis_result)
        recipients=analysis_result["destinataires"]
        print(recipients)
        match["Publicity"]=eval(analysis_result["Publicity"]) 
        # for obj in recipients:
        #     st.write(obj["recipient_address"])
        # Check if all recipient_address fields are not null using lambda function
        if len(recipients)>0:
            match["unique_recipient"]=True
            valid_recipients = all(
                obj.get("adresse_destinataire") and
                (score := fuzz.token_set_ratio(obj["adresse_destinataire"],
                "60 RUE FRANCOIS 1ER 75008 PARIS")) >= 60
                for obj in recipients
             )
            #print("All recipient_address fields are not null:", valid_recipients)
            if valid_recipients:
                first_item = recipients[0]["organisme_destinataire"] + ' ' +recipients[0]["nom_personnel_destinataire"]
                match["Valid_recipients"]=valid_recipients
                match["First_recipient"]=first_item
                match["Recipients"]= recipients
                if len(recipients)>1:
                    # Calculate similarity using fuzz.token_set_ratio
                    similar_names = all(
                        fuzz.token_set_ratio(obj["nom_personnel_destinataire"] + obj["organisme_destinataire"], 
                        first_item) >= 70
                        for obj in recipients
                    )
                    match["unique_recipient"]=similar_names
                    #print("Similaire :",similar_names)
    except json.JSONDecodeError as jde:
        print(f"JSON decoding error: {jde}")
    except ValueError as ve:
        print(f"Value error: {ve}")
    # Add other specific exceptions here as needed
    except Exception as ex:  # Consider removing if you handle all expected errors
        print(f"An unexpected error occurred: {ex}")
        # It's good practice to log unexpected errors or re-raise them after logging
    return match
