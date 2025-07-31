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
1. **Classify the file** into one most relevant and descriptive category (e.g., "Invoices", "Presentations", "Python Code", "Family Photos").
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
