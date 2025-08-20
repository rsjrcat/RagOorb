import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FileWriter:
    """Utility class for writing generated files to the filesystem."""
    
    def __init__(self, base_path: str = "./"):
        self.base_path = Path(base_path).resolve()
    
    def write_files(self, files_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Write multiple files to the filesystem.
        
        Args:
            files_data: List of dictionaries with 'path' and 'content' keys
            
        Returns:
            Dictionary with success status and details
        """
        results = {
            "success": True,
            "files_written": [],
            "errors": [],
            "total_files": len(files_data)
        }
        
        for file_data in files_data:
            try:
                file_path = file_data.get("path", "")
                content = file_data.get("content", "")
                
                if not file_path:
                    results["errors"].append("Missing file path")
                    continue
                
                # Write the file
                success = self.write_single_file(file_path, content)
                
                if success:
                    results["files_written"].append(file_path)
                else:
                    results["errors"].append(f"Failed to write {file_path}")
                    
            except Exception as e:
                error_msg = f"Error processing file {file_data.get('path', 'unknown')}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Set overall success status
        results["success"] = len(results["errors"]) == 0
        
        return results
    
    def write_single_file(self, file_path: str, content: str) -> bool:
        """
        Write a single file to the filesystem.
        
        Args:
            file_path: Relative path from base_path
            content: File content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Resolve the full path
            full_path = self.base_path / file_path
            
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            return False
    
    def backup_existing_files(self, files_data: List[Dict[str, str]]) -> bool:
        """
        Create backups of existing files before overwriting.
        
        Args:
            files_data: List of dictionaries with 'path' and 'content' keys
            
        Returns:
            True if all backups successful, False otherwise
        """
        try:
            backup_dir = self.base_path / ".backups" / f"backup_{int(os.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for file_data in files_data:
                file_path = file_data.get("path", "")
                if not file_path:
                    continue
                
                full_path = self.base_path / file_path
                
                # Only backup if file exists
                if full_path.exists():
                    backup_path = backup_dir / file_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy existing file to backup location
                    with open(full_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
            
            logger.info(f"Created backup in: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backups: {str(e)}")
            return False
    
    def validate_file_paths(self, files_data: List[Dict[str, str]]) -> List[str]:
        """
        Validate file paths for security and correctness.
        
        Args:
            files_data: List of dictionaries with 'path' and 'content' keys
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for file_data in files_data:
            file_path = file_data.get("path", "")
            
            if not file_path:
                errors.append("Empty file path found")
                continue
            
            # Check for path traversal attempts
            if ".." in file_path or file_path.startswith("/"):
                errors.append(f"Invalid file path: {file_path}")
                continue
            
            # Ensure path is within allowed directories
            allowed_prefixes = ["src/", "public/", "components/", "pages/", "styles/", "utils/", "types/"]
            if not any(file_path.startswith(prefix) for prefix in allowed_prefixes):
                errors.append(f"File path not in allowed directory: {file_path}")
        
        return errors