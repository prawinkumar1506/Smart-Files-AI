# import os
# import shutil
# import json
# from pathlib import Path
# from typing import List, Dict, Any, Optional, Tuple
# import logging
# from datetime import datetime
# import re
# import mimetypes
# from collections import defaultdict
# from services.llm_client import LLMClient

# logger = logging.getLogger(__name__)

# class BatchLLMClassifier:
#     """LLM-powered batch file classifier - classifies all files in one request"""
    
#     def __init__(self, llm_client: LLMClient):
#         self.llm_client = llm_client

#     async def classify_all_files(self, files: List[Dict]) -> Dict[str, Dict]:
#         """
#         Classify all files using chunked requests to handle large batches.
#         Returns: {file_key: {classification, folder_name, confidence, reasoning}}
#         """
#         try:
#             # Handle large batches by chunking
#             chunk_size = 50  # Process 50 files at a time to avoid token limits
#             all_classifications = {}
            
#             if len(files) > chunk_size:
#                 logger.info(f"Large batch detected ({len(files)} files). Processing in chunks of {chunk_size}")
                
#                 for i in range(0, len(files), chunk_size):
#                     chunk = files[i:i + chunk_size]
#                     chunk_classifications = await self._classify_chunk(chunk, i)
#                     all_classifications.update(chunk_classifications)
                    
#                     logger.info(f"Processed chunk {i//chunk_size + 1}/{(len(files) + chunk_size - 1)//chunk_size}")
                
#                 return all_classifications
#             else:
#                 return await self._classify_chunk(files, 0)
                
#         except Exception as e:
#             logger.error(f"Error in batch classification: {str(e)}")
#             return self._create_fallback_classifications(files, 0)

#     async def _classify_chunk(self, files_chunk: List[Dict], start_index: int) -> Dict[str, Dict]:
#         """Classify a chunk of files"""
#         try:
#             files_data = {}
            
#             # Prepare chunk data with proper indexing
#             for idx, file_info in enumerate(files_chunk):
#                 file_key = f"file_{start_index + idx}"
#                 content = file_info.get('content', '')
                
#                 # Use shorter content snippets for large batches
#                 content_snippet = content[:300].strip() if content else ''
                
#                 files_data[file_key] = {
#                     'file_name': file_info['file_name'],
#                     'content_snippet': content_snippet,
#                     'content_length': len(content) if content else 0
#                 }

#             prompt = f"""
# You are an intelligent file organization system. Analyze these files based on their CONTENT and organize them efficiently.

# FILES TO ANALYZE:
# {json.dumps(files_data, indent=1)}

# INSTRUCTIONS:
# 1. **CONTENT-BASED CLASSIFICATION**: Analyze actual file content, not just names
# 2. **EFFICIENT GROUPING**: Group similar files together (3-8 files per folder)
# 3. **CLEAR FOLDER NAMES**: Use descriptive, plural names (e.g., "Data Scientists", "Marketing Professionals")
# 4. **HIGH CONFIDENCE**: Only group files when you're confident they belong together

# EXAMPLES:
# - Resumes: Group by role ("Software Engineers", "Data Scientists", "Product Managers")
# - Documents: Group by type ("Financial Reports", "Research Papers", "Legal Contracts")
# - Mixed content: Use broader categories ("Technical Documents", "Business Files")

# Return ONLY a compact JSON object:
# {{
#     "file_0": {{"folder_name": "Data Scientists", "category": "Data Scientist Resume", "confidence": 0.95, "reasoning": "Resume shows ML/analytics experience"}},
#     "file_1": {{"folder_name": "Data Scientists", "category": "ML Engineer Resume", "confidence": 0.90, "reasoning": "Resume emphasizes machine learning skills"}}
# }}"""

#             logger.info(f"Classifying chunk of {len(files_chunk)} files")

#             response_text = await self.llm_client.generate_answer(
#                 question="Classify these files for organization.",
#                 context=prompt
#             )

#             logger.debug(f"LLM response length: {len(response_text)} chars")
#             logger.debug(f"Response preview: {response_text[:200]}...")

#             # Robust JSON extraction
#             classifications = self._extract_json_from_response(response_text)
            
#             if not classifications:
#                 logger.warning("Failed to extract valid JSON, using fallback for chunk")
#                 return self._create_fallback_classifications(files_chunk, start_index)
            
#             logger.info(f"Successfully classified {len(classifications)} files in chunk")
#             return classifications

#         except Exception as e:
#             logger.error(f"Error classifying chunk: {str(e)}")
#             return self._create_fallback_classifications(files_chunk, start_index)

#     def _extract_json_from_response(self, response_text: str) -> Dict[str, Dict]:
#         """Robustly extract JSON from LLM response with multiple fallback methods"""
#         try:
#             # Method 1: Clean markdown formatting
#             cleaned_text = response_text.strip()
#             if cleaned_text.startswith("```json"):
#                 cleaned_text = cleaned_text[7:]
#             if cleaned_text.endswith("```"):
#                 cleaned_text = cleaned_text[:-3]
            
#             # Method 2: Find JSON boundaries
#             start_idx = cleaned_text.find('{')
#             if start_idx == -1:
#                 raise ValueError("No opening brace found")
            
#             # Find matching closing brace
#             brace_count = 0
#             end_idx = -1
#             for i in range(start_idx, len(cleaned_text)):
#                 if cleaned_text[i] == '{':
#                     brace_count += 1
#                 elif cleaned_text[i] == '}':
#                     brace_count -= 1
#                     if brace_count == 0:
#                         end_idx = i + 1
#                         break
            
#             if end_idx == -1:
#                 # Method 3: Try to repair incomplete JSON
#                 logger.warning("Could not find matching closing brace. Attempting to repair.")
#                 json_text = cleaned_text[start_idx:]
                
#                 # Find the last comma and assume the JSON is truncated after it.
#                 last_comma_index = json_text.rfind(',')
#                 last_brace_index = json_text.rfind('}')
                
#                 # If the last significant character is a comma, trim it and close the JSON
#                 if last_comma_index > last_brace_index:
#                     json_text = json_text[:last_comma_index]
                
#                 # Add missing closing braces
#                 open_braces = json_text.count('{')
#                 close_braces = json_text.count('}')
#                 if open_braces > close_braces:
#                     json_text += '}' * (open_braces - close_braces)
                
#                 return json.loads(json_text)

#             json_text = cleaned_text[start_idx:end_idx]
#             return json.loads(json_text)
            
#         except (json.JSONDecodeError, ValueError) as e:
#             logger.error(f"JSON extraction failed: {str(e)}")
#             logger.debug(f"Problematic response: {response_text[:500]}...")
#             return {}

#     def _create_fallback_classifications(self, files: List[Dict], start_index: int = 0) -> Dict[str, Dict]:
#         """Create minimal fallback classifications when LLM fails"""
#         classifications = {}
        
#         for idx, file_info in enumerate(files):
#             file_key = f"file_{start_index + idx}"
            
#             classifications[file_key] = {
#                 'folder_name': 'Unclassified',
#                 'category': 'Unclassified File',
#                 'confidence': 0.1,
#                 'reasoning': 'LLM classification failed - requires manual review'
#             }
        
#         return classifications

# class FileOrganiser:
#     """Main file organiser with batch processing capability"""
    
#     def __init__(self, vector_store, llm_client: LLMClient):
#         self.vector_store = vector_store
#         self.classifier = BatchLLMClassifier(llm_client)
    
#     async def analyze_folder_for_organisation(self, folder_id: int, dry_run: bool = True) -> Dict[str, Any]:
#         """
#         Analyze a folder and its subfolders for organization using batch classification
#         """
#         try:
#             logger.info(f"Analyzing folder {folder_id} for batch organization (dry_run: {dry_run})")
            
#             # Get folder info and all files
#             folder_info = await self.vector_store.get_folder_by_id(folder_id)
#             if not folder_info:
#                 raise ValueError(f"Folder {folder_id} not found")
            
#             files = await self.vector_store.get_files_in_folder_recursive(folder_id)
#             logger.info(f"Found {len(files)} files to analyze in batch")
            
#             if not files:
#                 return {
#                     'success': True,
#                     'message': 'No files found to organize',
#                     'classifications': [],
#                     'suggested_structure': {},
#                     'total_files': 0
#                 }
            
#             # Prepare files with content for batch processing
#             files_with_content = []
#             for file_info in files:
#                 try:
#                     content = await self.vector_store.get_file_content(file_info['id'])
#                     file_info['content'] = content
#                     files_with_content.append(file_info)
#                 except Exception as e:
#                     logger.warning(f"Could not get content for {file_info['file_path']}: {str(e)}")
#                     file_info['content'] = ""
#                     files_with_content.append(file_info)
            
#             # Batch classify ALL files in single LLM request
#             llm_classifications = await self.classifier.classify_all_files(files_with_content)
            
#             # Convert LLM results to our format
#             classifications = []
#             folder_structure = defaultdict(list)
            
#             for idx, file_info in enumerate(files_with_content):
#                 file_key = f"file_{idx}"
#                 llm_result = llm_classifications.get(file_key, {})
                
#                 classification = {
#                     'file_id': file_info['id'],
#                     'file_path': file_info['file_path'],
#                     'file_name': file_info['file_name'],
#                     'file_type': file_info.get('file_type', ''),
#                     'classification': llm_result.get('category', 'miscellaneous'),
#                     'confidence': llm_result.get('confidence', 0.5),
#                     'suggested_folder': llm_result.get('folder_name', 'Miscellaneous'),
#                     'reasoning': llm_result.get('reasoning', 'No reasoning provided')
#                 }
                
#                 classifications.append(classification)
#                 folder_structure[classification['suggested_folder']].append(file_info['file_name'])
            
#             suggested_structure = dict(folder_structure)
            
#             logger.info(f"Batch analysis complete: {len(classifications)} files classified into {len(suggested_structure)} folders")
            
#             return {
#                 'success': True,
#                 'message': f'Batch analyzed {len(files)} files and found {len(suggested_structure)} organization opportunities',
#                 'classifications': classifications,
#                 'suggested_structure': suggested_structure,
#                 'total_files': len(files),
#                 'batch_processed': True
#             }
            
#         except Exception as e:
#             logger.error(f"Error in batch folder analysis: {str(e)}")
#             raise
    
#     async def execute_organisation(self, folder_id: int, classifications: List[Dict], confirm: bool = False) -> Dict[str, Any]:
#         """
#         Execute the file organization based on batch classifications
#         """
#         if not confirm:
#             return {
#                 'success': False,
#                 'message': 'Organization requires user confirmation',
#                 'actions_needed': len(classifications)
#             }
        
#         try:
#             logger.info(f"Executing batch organization for folder {folder_id} with {len(classifications)} files")
            
#             folder_info = await self.vector_store.get_folder_by_id(folder_id)
#             base_path = Path(folder_info['path'])
            
#             actions_log = []
#             created_folders = set()
#             moved_files = []
            
#             # Group by folder (including subfolders)
#             folder_groups = defaultdict(list)
#             for classification in classifications:
#                 folder_groups[classification['suggested_folder']].append(classification)
            
#             # Process each folder group
#             for folder_path, file_classifications in folder_groups.items():
#                 try:
#                     # Handle nested folders (e.g., "Documents/Invoices")
#                     folder_parts = folder_path.split('/')
#                     current_path = base_path
                    
#                     # Create nested directory structure
#                     for part in folder_parts:
#                         current_path = current_path / part
#                         if not current_path.exists():
#                             current_path.mkdir(parents=True, exist_ok=True)
#                             created_folders.add(str(current_path))
#                             logger.info(f"Created folder: {current_path}")
                            
#                             # Add to database
#                             await self.vector_store.add_subfolder(folder_id, str(current_path), part)
                    
#                     target_folder = current_path
                    
#                     # Move files to target folder
#                     for classification in file_classifications:
#                         source_path = Path(classification['file_path'])
#                         target_path = target_folder / source_path.name
                        
#                         if source_path.exists() and source_path != target_path:
#                             # Handle name conflicts
#                             counter = 1
#                             original_target = target_path
#                             while target_path.exists():
#                                 stem = original_target.stem
#                                 suffix = original_target.suffix
#                                 target_path = target_folder / f"{stem}_{counter}{suffix}"
#                                 counter += 1
                            
#                             # Move the file
#                             shutil.move(str(source_path), str(target_path))
#                             moved_files.append({
#                                 'source': str(source_path),
#                                 'target': str(target_path),
#                                 'folder': folder_path,
#                                 'classification': classification['classification']
#                             })
                            
#                             # Update database
#                             await self.vector_store.update_file_location(
#                                 classification['file_id'], 
#                                 str(target_path)
#                             )
                            
#                             # Log action
#                             action = {
#                                 'action_type': 'move',
#                                 'source_path': str(source_path),
#                                 'target_path': str(target_path),
#                                 'folder_path': folder_path,
#                                 'classification': classification['classification'],
#                                 'confidence': classification['confidence'],
#                                 'timestamp': datetime.now(),
#                                 'status': 'completed'
#                             }
#                             actions_log.append(action)
                            
#                             logger.info(f"Moved {source_path.name} to {folder_path}")
                
#                 except Exception as e:
#                     logger.error(f"Error organizing files in {folder_path}: {str(e)}")
#                     # Log failed actions
#                     for classification in file_classifications:
#                         action = {
#                             'action_type': 'move',
#                             'source_path': classification.get('file_path', 'unknown'),
#                             'target_path': folder_path,
#                             'classification': classification.get('classification', 'unknown'),
#                             'confidence': classification.get('confidence', 0),
#                             'timestamp': datetime.now(),
#                             'status': 'failed',
#                             'error': str(e)
#                         }
#                         actions_log.append(action)
#                     continue
            
#             # Save actions for potential rollback
#             await self.vector_store.save_organisation_actions(folder_id, actions_log)
            
#             # Refresh folder structure in database
#             await self.vector_store.get_indexed_folders()
            
#             logger.info(f"Batch organization complete: {len(moved_files)} files moved, {len(created_folders)} folders created")
            
#             return {
#                 'success': True,
#                 'message': f'Successfully organized {len(moved_files)} files into {len(created_folders)} folders using batch processing',
#                 'moved_files': len(moved_files),
#                 'created_folders': len(created_folders),
#                 'folder_structure': list(folder_groups.keys()),
#                 'actions_log': actions_log,
#                 'batch_processed': True
#             }
            
#         except Exception as e:
#             logger.error(f"Error executing batch organization: {str(e)}")
#             # Attempt rollback
#             try:
#                 await self._rollback_actions(actions_log)
#             except Exception as rollback_error:
#                 logger.error(f"Rollback failed: {str(rollback_error)}")
#             raise
    
#     async def _rollback_actions(self, actions_log: List[Dict]) -> None:
#         """Rollback organization actions in case of error"""
#         logger.info("Attempting to rollback batch organization actions")
        
#         for action in reversed(actions_log):
#             try:
#                 if action['action_type'] == 'move' and action['status'] == 'completed':
#                     source_path = Path(action['target_path'])
#                     target_path = Path(action['source_path'])
                    
#                     if source_path.exists():
#                         # Ensure target directory exists
#                         target_path.parent.mkdir(parents=True, exist_ok=True)
#                         shutil.move(str(source_path), str(target_path))
#                         logger.info(f"Rolled back: {source_path.name}")
                        
#                         # Update database
#                         await self.vector_store.update_file_location_by_path(
#                             str(source_path), str(target_path)
#                         )
                        
#             except Exception as e:
#                 logger.error(f"Error rolling back action: {str(e)}")
#                 continue

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
from services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class LLMClassifier:
    """LLM-powered file classifier"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def classify_file(self, file_path: str, file_content: str = "") -> Tuple[str, float, str, str]:
        """
        Classify a file and suggest a folder name using an LLM.
        Returns: (classification, confidence, reasoning, suggested_folder)
        """
        try:
            file_name = Path(file_path).name
            content_snippet = file_content[:500].strip()

            prompt = f"""
Analyze the following file and determine the most appropriate category and folder name for effective organization.

File Details:
- File Name: {file_name}
- File Content Snippet:
---
{content_snippet if content_snippet else "Content not available"}
---

Instructions:
1. **Classify the file** into one most relevant and descriptive category.
   - For code files, use the language name (e.g., "Python Code", "JavaScript Code", "C Code"). Recognize .py, .c, .ts, .html, .css, .tsx as code.
   - For other files, use descriptive categories (e.g., "Invoices", "Presentations", "Family Photos", "Database File"). Recognize .db as a database file.
2. **Recommend a folder name** that is short, clear, and contextually appropriate for storing similar files.
3. **Justify your classification** with a concise explanation based on the file name and content snippet.
4. **Assign a confidence score** (from 0.0 to 1.0) that reflects the certainty of your classification.

Respond strictly in the following JSON format:
{{
    "category": "your_category",
    "folder_name": "Suggested Folder Name",
    "confidence": 0.9,
    "reasoning": "your_brief_reasoning"
}}
"""

            logger.debug(f"🔍 Classifying file: {file_name} with prompt:\n{prompt}")

            response_text = await self.llm_client.generate_answer(
                question="Classify this file for organization.",
                context=prompt
            )

            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain valid JSON.")
            
            response_json = json.loads(json_match.group())

            category = response_json.get("category", "miscellaneous")
            folder_name = response_json.get("folder_name", "Miscellaneous")
            confidence = float(response_json.get("confidence", 0.5))
            reasoning = response_json.get("reasoning", "No reasoning provided by LLM.")

            logger.debug(f"LLM classified {file_name} as {category} (confidence: {confidence:.2f})")
            
            return category, confidence, reasoning, folder_name

        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from LLM response for {file_path}")
            return 'miscellaneous', 0.2, "Failed to parse LLM response", "Miscellaneous"
        except Exception as e:
            logger.error(f"Error classifying file {file_path} with LLM: {str(e)}")
            return 'miscellaneous', 0.1, f"LLM classification error: {str(e)}", "Miscellaneous"

class FileOrganiser:
    """Main file organiser that handles the complete organization workflow"""
    
    def __init__(self, vector_store, llm_client: LLMClient):
        self.vector_store = vector_store
        self.classifier = LLMClassifier(llm_client)
    
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
                    content = await self.vector_store.get_file_content(file_info['id'])
                    
                    category, confidence, reasoning, suggested_folder = await self.classifier.classify_file(
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
                        'suggested_folder': suggested_folder,
                        'reasoning': reasoning
                    }
                    
                    classifications.append(classification)
                    category_files[suggested_folder].append(file_info['file_name'])
                    
                except Exception as e:
                    logger.error(f"Error classifying file {file_info['file_path']}: {str(e)}")
                    continue
            
            # The suggested structure is now directly generated from the LLM's suggestions
            suggested_structure = {k: v for k, v in category_files.items()}
            
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

            # Recalculate file counts
            await self.vector_store.get_indexed_folders()
            
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
