from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.smart_images_service import SmartImagesService
import logging

router = APIRouter()
smart_images_service = SmartImagesService()

logger = logging.getLogger(__name__)

@router.get("/api/images")
async def get_indexed_images():
    """Fetch all indexed images from the vector store."""
    try:
        images = await smart_images_service.get_indexed_images()
        return {"success": True, "images": images}
    except Exception as e:
        logger.error(f"Error fetching indexed images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/images/search")
async def search_images(query: Dict):
    """Search images by text query using CLIP embeddings."""
    try:
        search_query = query.get("query", "")
        if not search_query.strip():
            return {"success": False, "message": "Empty search query"}

        images = await smart_images_service.search_images(search_query)
        return {"success": True, "images": images}
    except Exception as e:
        logger.error(f"Error searching images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/images/rename")
async def rename_image(request: Dict):
    """Rename an image and update its metadata."""
    try:
        image_id = request.get("image_id")
        new_name = request.get("new_name")
        if image_id is None or new_name is None:
            raise HTTPException(status_code=400, detail="Missing image_id or new_name")

        success = smart_images_service.rename_image(image_id, new_name)
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")

        return {"success": True, "message": "Image renamed successfully"}
    except Exception as e:
        logger.error(f"Error renaming image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/index/folder")
async def index_folder(request: Dict):
    """Index a folder containing image files."""
    try:
        folder_path = request.get("folderPath")
        if folder_path is None:
            raise HTTPException(status_code=400, detail="Missing folderPath")

        indexed_images = await smart_images_service.index_folder(folder_path)
        return {"success": True, "indexed_images": indexed_images}
    except Exception as e:
        logger.error(f"Error indexing folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
