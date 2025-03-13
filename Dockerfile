# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.9

# Set the working directory
WORKDIR /var/task

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set the Lambda entrypoint
CMD ["app.main.handler"]
