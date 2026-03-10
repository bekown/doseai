# app/utils/file_upload.py

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

class FileUploadService:
    """Service for handling file uploads"""
    
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'reports': {'pdf', 'doc', 'docx', 'xls', 'xlsx'},
        'all': {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx'}
    }
    
    @staticmethod
    def allowed_file(filename, file_type='all'):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in FileUploadService.ALLOWED_EXTENSIONS.get(file_type, FileUploadService.ALLOWED_EXTENSIONS['all'])
    
    @staticmethod
    def generate_filename(original_filename, prefix=''):
        """Generate a unique filename"""
        ext = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        if prefix:
            filename = f"{prefix}_{timestamp}_{unique_id}.{ext}"
        else:
            filename = f"{timestamp}_{unique_id}.{ext}"
        
        return secure_filename(filename)
    
    @staticmethod
    def save_uploaded_file(file, subfolder='', file_type='all', user_id=None):
        """
        Save uploaded file to appropriate location
        
        Returns:
            tuple: (success, file_path_or_error_message)
        """
        if not file or file.filename == '':
            return False, 'No file selected'
        
        if not FileUploadService.allowed_file(file.filename, file_type):
            return False, f'File type not allowed. Allowed: {", ".join(FileUploadService.ALLOWED_EXTENSIONS[file_type])}'
        
        # Generate unique filename
        prefix = f"user_{user_id}" if user_id else ""
        filename = FileUploadService.generate_filename(file.filename, prefix)
        
        # Create upload directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if subfolder:
            upload_path = os.path.join(upload_folder, subfolder)
        else:
            upload_path = upload_folder
        
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Return relative path for database storage
        relative_path = os.path.join(subfolder, filename) if subfolder else filename
        return True, relative_path
    
    @staticmethod
    def delete_file(file_path):
        """Delete a file from storage"""
        try:
            full_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            current_app.logger.error(f"Error deleting file {file_path}: {e}")
        return False
    
    @staticmethod
    def get_file_url(file_path):
        """Get URL for a stored file"""
        if not file_path:
            return None
        
        # In production, this might point to cloud storage
        # For development, serve from uploads folder
        return f"/uploads/{file_path}"