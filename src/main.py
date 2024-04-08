"""Module docstring: This module contains functions for analyzing PDF images and verifying 
recipients."""
import time
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import mangum
from gcv import analyze_pdf_images, verifify_recipents_json
from openai_helpers import analyze_image_with_openai

app = FastAPI()
#Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin, you may want to restrict this
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Wrap FastAPI app with Mangum for use with AWS Lambda
handler = mangum.Mangum(app)

@app.get("/", include_in_schema=False)
async def redirect_to_redoc():
    """Redirects to the API documentation (Redoc)."""
    return RedirectResponse(url="/docs")

@app.get("/test")
async def test_endpoint():
    """This function returns a test message."""
    return {"message": "This is a test endpoint"}

@app.get("/analyze-pdf")
async def analyze_pdf(url: str):
    """This function analyzes PDF images."""
    try:
        start_time = time.time()  # Start the timer
        #analysis_result,tokens,nbr_imgs,time_cvr_image,time_openai = analyze_pdf_images(url)
        result1 = analyze_pdf_images(url)
        result=verifify_recipents_json(result1[0])
        # Calculate the total processing time
        total_processing_time = time.time() - start_time
        print("total_processing_time:",total_processing_time)
        new_data = {
        "Speed": {
            "Convert PDF to image": result1[3],
            "GPT-4 Inference Time": result1[4],
            "Total processing Time":total_processing_time,
            "Number images": result1[2],
            "Tokens used": result1[1],
            "Cost ":f"{result1[1] * 0.00001:.3f}$"

        }}
         # Update the existing result with the new data
        result.update(new_data)
        return result
    except Exception as e:  # Catching any other exceptions
        # Log the error or return a generic error response
        print(f"An unexpected error occurred: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}, {result1}"}   

@app.get("/analyze-image")
async def analyze_image(path: str="document_image.jpeg"):
    """This function analyze PDF image."""
    try:
        return {"result": analyze_image_with_openai(path,url=False)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during image analysis.") from e   
# @app.get("/analyze-image-url")
# async def analyze_images_url(url: str):
#     """This function analyze image from URL."""
#     try:
#         url="document_image.jpeg"
#         return {"result": analyze_image_with_openai(url,url=True)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="An error occurred during image analysis.") from e
