# Use the official AWS Lambda base image for Python
FROM public.ecr.aws/lambda/python:3.11

# Copy your Lambda function code into the container
COPY src/* ${LAMBDA_TASK_ROOT}
# Copy requirements.txt and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Set the CMD to your handler (could be different based on your setup)
CMD ["main.handler"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
