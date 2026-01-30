"""Google Drive Uploader for Market Scanner reports."""

import os
import json
from datetime import datetime
from typing import Optional

from ..config import GDRIVE_ROOT_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_JSON, UPLOAD_TO_GDRIVE


class GoogleDriveUploader:
    """Uploads PDF reports to Google Drive."""

    def __init__(self):
        self.enabled = UPLOAD_TO_GDRIVE and GOOGLE_SERVICE_ACCOUNT_JSON and GDRIVE_ROOT_FOLDER_ID
        self.service = None
        self.root_folder_id = GDRIVE_ROOT_FOLDER_ID
        
        if self.enabled:
            self._init_service()

    def _init_service(self):
        """Initialize Google Drive service."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES
            )
            self.service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"[Warning] Failed to initialize Google Drive service: {e}")
            self.enabled = False

    def upload_report(self, pdf_path: str, date: datetime = None) -> Optional[dict]:
        """Upload PDF directly to the shared folder."""
        if not self.enabled:
            print("[Info] Google Drive upload disabled or not configured")
            return None
        
        if date is None:
            date = datetime.now()
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            # File name: "2026-01-29-Wed-Market-Scan.pdf"
            file_name = f"{date.strftime('%Y-%m-%d-%a')}-Market-Scan.pdf"
            
            # Upload directly to the shared folder (no subfolders)
            # This works because the folder is owned by the user, not the service account
            file_metadata = {
                'name': file_name,
                'parents': [self.root_folder_id]
            }
            
            media = MediaFileUpload(pdf_path, mimetype='application/pdf')
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"[Info] Uploaded to Drive: {file['name']}")
            
            return {
                'id': file['id'],
                'name': file['name'],
                'link': file['webViewLink']
            }
        except Exception as e:
            print(f"[Error] Failed to upload to Google Drive: {e}")
            return None
