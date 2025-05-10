import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from datetime import datetime


def upload_to_folder(folder_id, file_name):
    """Upload a file to the specified folder and return the file ID."""
    try:
        # Use the API key from environment variables
        creds, _ = google.auth.default()

        # Create Drive API client
        service = build("drive", "v3", credentials=creds)
        
        # Add date to the filename
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_name_with_date = f"{file_name}_{current_date}"
        
        # Create file metadata with the date-included filename and folder ID
        file_metadata = {"name": file_name_with_date, "parents": [folder_id]}
        
        # Create media with the PDF file and appropriate mimetype
        media = MediaFileUpload(file_name, mimetype="application/pdf", resumable=True)

        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f'File ID: "{file.get("id")}".')
        print(f'Uploaded as: "{file_name_with_date}"')
        return file.get("id")
                
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
