import os
import logging
import glob
from pathlib import Path

logger = logging.getLogger(__name__)

class FileOperations:
    def __init__(self, base_path="/"):
        self.base_path = base_path

    def list_directory(self, path="."):
        """List contents of a directory"""
        try:
            full_path = os.path.join(self.base_path, path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Path does not exist: {full_path}")
            
            if not os.path.isdir(full_path):
                raise NotADirectoryError(f"Path is not a directory: {full_path}")
            
            entries = []
            for entry in os.listdir(full_path):
                entry_path = os.path.join(full_path, entry)
                if os.path.isdir(entry_path):
                    entries.append(f"📁 {entry}/")
                else:
                    size = os.path.getsize(entry_path)
                    entries.append(f"📄 {entry} ({self._format_size(size)})")
            
            return entries
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise

    def file_exists(self, file_path):
        """Check if a file exists"""
        full_path = os.path.join(self.base_path, file_path)
        return os.path.exists(full_path) and os.path.isfile(full_path)

    def delete_file(self, file_path):
        """Delete a file"""
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            return True
        return False

    def search_files(self, query, search_path="."):
        """Search for files matching a query"""
        try:
            full_path = os.path.join(self.base_path, search_path)
            if not os.path.exists(full_path):
                return []
            
            pattern = f"{full_path}/**/*{query}*"
            matches = glob.glob(pattern, recursive=True)
            
            results = []
            for match in matches:
                relative_path = os.path.relpath(match, self.base_path)
                if os.path.isfile(match):
                    size = os.path.getsize(match)
                    results.append(f"📄 {relative_path} ({self._format_size(size)})")
                else:
                    results.append(f"📁 {relative_path}/")
            
            return results[:100]  # Limit to 100 results
        except Exception as e:
            logger.error(f"Error searching files for {query}: {e}")
            return []

    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"