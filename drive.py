import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload



def upload_to_folder(folder_id, file_name):
    """Upload a file to the specified folder and return the file ID."""
    try:
        # Use the API key from environment variables
        creds, _ = google.auth.default()

        # Create Drive API client
        service = build("drive", "v3", credentials=creds)
        
        # Create file metadata with the actual filename and folder ID
        file_metadata = {"name": file_name, "parents": [folder_id]}
        
        # Create media with the PDF file and appropriate mimetype
        media = MediaFileUpload(file_name, mimetype="application/pdf", resumable=True)

        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f'File ID: "{file.get("id")}".')
        return file.get("id")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
