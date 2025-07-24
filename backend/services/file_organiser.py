import os
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import re
import mimetypes
from collections import defaultdict

logger = logging.getLogger(__name__)

class FileClassifier:
    """AI-powered file classifier that analyzes files and suggests organization"""
    
    def __init__(self):
        self.classification_rules = {
            'documents': {
                'patterns': [r'\.pdf$', r'\.docx?$', r'\.txt$', r'\.rtf$', r'\.odt$'],
                'keywords': ['document', 'report', 'manual', 'guide', 'specification'],
                'content_keywords': ['contract', 'agreement', 'policy', 'procedure']
            },
            'invoices': {
                'patterns': [r'invoice', r'bill', r'receipt', r'payment'],
                'keywords': ['invoice', 'bill', 'receipt', 'payment', 'charge'],
                'content_keywords': ['total', 'amount', 'due', 'invoice', 'billing']
            },
            'reports': {
                'patterns': [r'report', r'analysis', r'summary', r'review'],
                'keywords': ['report', 'analysis', 'summary', 'review', 'findings'],
                'content_keywords': ['conclusion', 'recommendation', 'analysis', 'findings']
            },
            'presentations': {
                'patterns': [r'\.pptx?$', r'\.key$', r'\.odp$'],
                'keywords': ['presentation', 'slides', 'deck', 'pitch'],
                'content_keywords': ['slide', 'presentation', 'overview']
            },
            'spreadsheets': {
                'patterns': [r'\.xlsx?$', r'\.csv$', r'\.ods$'],
                'keywords': ['spreadsheet', 'data', 'calculation', 'budget'],
                'content_keywords': ['total', 'sum', 'calculation', 'budget']
            },
            'images': {
                'patterns': [r'\.jpe?g$', r'\.png$', r'\.gif$', r'\.bmp$', r'\.svg$', r'\.tiff?$'],
                'keywords': ['image', 'photo', 'picture', 'graphic'],
                'content_keywords': []
            },
            'videos': {
                'patterns': [r'\.mp4$', r'\.avi$', r'\.mov$', r'\.wmv$', r'\.flv$', r'\.mkv$'],
                'keywords': ['video', 'movie', 'clip', 'recording'],
                'content_keywords': []
            },
            'audio': {
                'patterns': [r'\.mp3$', r'\.wav$', r'\.flac$', r'\.aac$', r'\.ogg$'],
                'keywords': ['audio', 'music', 'sound', 'recording'],
                'content_keywords': []
            },
            'code': {
                'patterns': [r'\.py$', r'\.js$', r'\.html$', r'\.css$', r'\.java$', r'\.cpp$', r'\.c$'],
                'keywords': ['code', 'script', 'program', 'source'],
                'content_keywords': ['function', 'class', 'import', 'def', 'var']
            },
            'archives': {
                'patterns': [r'\.zip$', r'\.rar$', r'\.7z$', r'\.tar$', r'\.gz$'],
                'keywords': ['archive', 'backup', 'compressed'],
                'content_keywords': []
            },
            'certificates': {
                'patterns': [r'certificate', r'cert', r'diploma', r'award'],
                'keywords': ['certificate', 'certification', 'diploma', 'award', 'qualification'],
                'content_keywords': ['certified', 'completion', 'achievement', 'qualification']
            }
        }
    
    async def classify_file(self, file_path: str, file_content: str = "") -> Tuple[str, float, str]:
        """
        Classify a file based on its path, name, and content
        Returns: (classification, confidence, reasoning)
        """
        try:
            file_path_lower = file_path.lower()
            file_name = Path(file_path).name.lower()
            
            scores = defaultdict(float)
            reasoning_parts = []
            
            # Analyze file extension and patterns
            for category, rules in self.classification_rules.items():
                category_score = 0
                category_reasons = []
                
                # Check file patterns
                for pattern in rules['patterns']:
                    if re.search(pattern, file_path_lower, re.IGNORECASE):
                        category_score += 0.4
                        category_reasons.append(f"matches {pattern} pattern")
                
                # Check filename keywords
                for keyword in rules['keywords']:
                    if keyword in file_name:
                        category_score += 0.3
                        category_reasons.append(f"filename contains '{keyword}'")
                
                # Check content keywords (if content available)
                if file_content:
                    content_lower = file_content.lower()
                    for keyword in rules['content_keywords']:
                        if keyword in content_lower:
                            category_score += 0.2
                            category_reasons.append(f"content contains '{keyword}'")
                
                if category_score > 0:
                    scores[category] = min(category_score, 1.0)  # Cap at 1.0
                    reasoning_parts.append(f"{category}: {', '.join(category_reasons)}")
            
            # Determine best classification
            if not scores:
                return 'miscellaneous', 0.1, "No specific patterns matched"
            
            best_category = max(scores.keys(), key=lambda k: scores[k])
            confidence = scores[best_category]
            reasoning = f"Classified as {best_category} because: {'; '.join(reasoning_parts)}"
            
            logger.debug(f"Classified {file_name} as {best_category} (confidence: {confidence:.2f})")
            
            return best_category, confidence, reasoning
            
        except Exception as e:
            logger.error(f"Error classifying file {file_path}: {str(e)}")
            return 'miscellaneous', 0.1, f"Classification error: {str(e)}"
    
    def generate_folder_name(self, category: str, files: List[str]) -> str:
        """Generate a meaningful folder name based on classification and files"""
        
        # Special naming rules for certain categories
        folder_names = {
            'invoices': 'Invoices & Bills',
            'reports': 'Reports & Analysis',
            'presentations': 'Presentations & Slides',
            'spreadsheets': 'Spreadsheets & Data',
            'images': 'Images & Photos',
            'videos': 'Videos & Media',
            'audio': 'Audio & Music',
            'code': 'Code & Scripts',
            'archives': 'Archives & Backups',
            'certificates': 'Certificates & Awards',
            'documents': 'Documents',
            'miscellaneous': 'Other Files'
        }
        
        base_name = folder_names.get(category, category.title())
        
        # Add date suffix if there are many files
        if len(files) > 20:
            date_suffix = datetime.now().strftime("%Y-%m")
            return f"{base_name} ({date_suffix})"
        
        return base_name

class FileOrganiser:
    """Main file organiser that handles the complete organization workflow"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.classifier = FileClassifier()
    
    async def analyze_folder_for_organisation(self, folder_id: int, dry_run: bool = True) -> Dict[str, Any]:
        """
        Analyze a folder and its subfolders for organization opportunities
        """
        try:
            logger.info(f"🔍 Analyzing folder {folder_id} for organization (dry_run: {dry_run})")
            
            # Get folder info and all files
            folder_info = await self.vector_store.get_folder_by_id(folder_id)
            if not folder_info:
                raise ValueError(f"Folder {folder_id} not found")
            
            files = await self.vector_store.get_files_in_folder_recursive(folder_id)
            logger.info(f"📊 Found {len(files)} files to analyze")
            
            if not files:
                return {
                    'success': True,
                    'message': 'No files found to organize',
                    'classifications': [],
                    'suggested_structure': {},
                    'total_files': 0
                }
            
            # Classify each file
            classifications = []
            category_files = defaultdict(list)
            
            for file_info in files:
                try:
                    # Get file content if available
                    content = await self.vector_store.get_file_content(file_info['id'])
                    
                    # Classify the file
                    category, confidence, reasoning = await self.classifier.classify_file(
                        file_info['file_path'], 
                        content or ""
                    )
                    
                    classification = {
                        'file_id': file_info['id'],
                        'file_path': file_info['file_path'],
                        'file_name': file_info['file_name'],
                        'file_type': file_info['file_type'],
                        'classification': category,
                        'confidence': confidence,
                        'suggested_folder': self.classifier.generate_folder_name(category, [file_info['file_name']]),
                        'reasoning': reasoning
                    }
                    
                    classifications.append(classification)
                    category_files[category].append(file_info['file_name'])
                    
                except Exception as e:
                    logger.error(f"Error classifying file {file_info['file_path']}: {str(e)}")
                    continue
            
            # Generate suggested folder structure
            suggested_structure = {}
            for category, file_list in category_files.items():
                folder_name = self.classifier.generate_folder_name(category, file_list)
                suggested_structure[folder_name] = file_list
            
            logger.info(f"✅ Analysis complete: {len(classifications)} files classified into {len(suggested_structure)} categories")
            
            return {
                'success': True,
                'message': f'Analyzed {len(files)} files and found {len(suggested_structure)} organization opportunities',
                'classifications': classifications,
                'suggested_structure': suggested_structure,
                'total_files': len(files)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing folder for organization: {str(e)}")
            raise
    
    async def execute_organisation(self, folder_id: int, classifications: List[Dict], confirm: bool = False) -> Dict[str, Any]:
        """
        Execute the file organization based on classifications
        """
        if not confirm:
            return {
                'success': False,
                'message': 'Organization requires user confirmation',
                'actions_needed': len(classifications)
            }
        
        try:
            logger.info(f"🚀 Executing organization for folder {folder_id} with {len(classifications)} files")
            
            folder_info = await self.vector_store.get_folder_by_id(folder_id)
            base_path = Path(folder_info['path'])
            
            actions_log = []
            created_folders = set()
            moved_files = []
            
            # Group classifications by suggested folder
            folder_groups = defaultdict(list)
            for classification in classifications:
                folder_groups[classification['suggested_folder']].append(classification)
            
            # Create folders and move files
            for folder_name, file_classifications in folder_groups.items():
                try:
                    # Create target folder
                    target_folder = base_path / folder_name
                    if not target_folder.exists():
                        target_folder.mkdir(parents=True, exist_ok=True)
                        created_folders.add(str(target_folder))
                        logger.info(f"📁 Created folder: {target_folder}")
                        
                        # Add folder to database
                        await self.vector_store.add_subfolder(folder_id, str(target_folder), folder_name)
                    
                    # Move files to the folder
                    for classification in file_classifications:
                        source_path = Path(classification['file_path'])
                        target_path = target_folder / source_path.name
                        
                        if source_path.exists() and source_path != target_path:
                            # Move the file
                            shutil.move(str(source_path), str(target_path))
                            moved_files.append({
                                'source': str(source_path),
                                'target': str(target_path),
                                'classification': classification['classification']
                            })
                            
                            # Update database
                            await self.vector_store.update_file_location(
                                classification['file_id'], 
                                str(target_path)
                            )
                            
                            # Log the action
                            action = {
                                'action_type': 'move',
                                'source_path': str(source_path),
                                'target_path': str(target_path),
                                'classification': classification['classification'],
                                'confidence': classification['confidence'],
                                'timestamp': datetime.now(),
                                'status': 'completed'
                            }
                            actions_log.append(action)
                            
                            logger.info(f"📦 Moved {source_path.name} to {folder_name}")
                
                except Exception as e:
                    logger.error(f"❌ Error organizing files in {folder_name}: {str(e)}")
                    # Log failed action
                    action = {
                        'action_type': 'move',
                        'source_path': classification.get('file_path', 'unknown'),
                        'target_path': str(target_folder),
                        'classification': classification.get('classification', 'unknown'),
                        'confidence': classification.get('confidence', 0),
                        'timestamp': datetime.now(),
                        'status': 'failed',
                        'error': str(e)
                    }
                    actions_log.append(action)
                    continue
            
            # Save actions to database for potential rollback
            await self.vector_store.save_organisation_actions(folder_id, actions_log)
            
            logger.info(f"✅ Organization complete: {len(moved_files)} files moved, {len(created_folders)} folders created")
            
            return {
                'success': True,
                'message': f'Successfully organized {len(moved_files)} files into {len(created_folders)} folders',
                'moved_files': len(moved_files),
                'created_folders': len(created_folders),
                'actions_log': actions_log
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing organization: {str(e)}")
            # Attempt rollback on error
            try:
                await self._rollback_actions(actions_log)
            except Exception as rollback_error:
                logger.error(f"❌ Rollback failed: {str(rollback_error)}")
            raise
    
    async def _rollback_actions(self, actions_log: List[Dict]) -> None:
        """Rollback organization actions in case of error"""
        logger.info("🔄 Attempting to rollback organization actions")
        
        for action in reversed(actions_log):
            try:
                if action['action_type'] == 'move' and action['status'] == 'completed':
                    source_path = Path(action['target_path'])
                    target_path = Path(action['source_path'])
                    
                    if source_path.exists():
                        shutil.move(str(source_path), str(target_path))
                        logger.info(f"🔄 Rolled back: {source_path.name}")
                        
                        # Update database
                        await self.vector_store.update_file_location_by_path(
                            str(source_path), str(target_path)
                        )
                        
            except Exception as e:
                logger.error(f"❌ Error rolling back action: {str(e)}")
                continue
