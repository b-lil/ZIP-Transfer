import azure.functions as func
import logging
import zipfile
import os
import tempfile
from azure.storage.blob import BlobServiceClient
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing ZIP creation request.")

    try:
        files = req.files.getlist("files")  # Multiple files input
        password = req.form.get("password")  # Optional password

        if not files:
            return func.HttpResponse(json.dumps({"error": "No files uploaded"}), mimetype="application/json", status_code=400)

        # Create a temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")

        # Create ZIP archive
        with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                zipf.writestr(file.filename, file.read())  # Add file to ZIP

            if password:
                zipf.setpassword(password.encode())  # Set password if provided

        # Upload ZIP to Azure Blob Storage
        AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=rgfunctions001891a;AccountKey=j+SUA0t22Td5NdsI6pDrWmCn6QEXtXcswJf386nvTXtgi7qiIPxuwY7fy+dbkmHMMWLSjIwnnL0c+AStDl6tUQ==;EndpointSuffix=core.windows.net"
        CONTAINER_NAME = "zipped-files"

        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=os.path.basename(temp_zip.name))

        with open(temp_zip.name, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Generate public URL for download
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{os.path.basename(temp_zip.name)}"

        return func.HttpResponse(json.dumps({"zip_url": blob_url}), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)
