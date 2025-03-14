#python image
FROM python:3.12

#environment variable
ENV PYTHONUNBUFFERED=1

#working directory
WORKDIR /app

#copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Django
EXPOSE 8000

# Start the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]