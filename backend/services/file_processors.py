#backend\services\file_processors.py
import os
import json
import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Dict
import logging

logger = logging.getLogger(__name__)

class FileProcessor(Protocol):
    async def extract_text(self, file_path: Path) -> str:
        """Extract text content from a file"""
        ...

class TextFileProcessor:
    """Processor for plain text files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            return ""

class PDFProcessor:
    """Processor for PDF files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed, skipping PDF processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {str(e)}")
            return ""

class DocxProcessor:
    """Processor for DOCX files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed, skipping DOCX processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {str(e)}")
            return ""

class CSVProcessor:
    """Processor for CSV/TSV files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8', errors='ignore', newline='') as f:
                sample = f.read(2048)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except Exception:
                    dialect = csv.excel
                reader = csv.reader(f, dialect)
                rows = []
                for row in reader:
                    row_text = "\t".join(cell.strip() for cell in row).strip()
                    if row_text:
                        rows.append(row_text)
                return "\n".join(rows)
        except Exception as e:
            logger.error(f"Error reading CSV/TSV file {file_path}: {str(e)}")
            return ""

class XLSXProcessor:
    """Processor for XLSX files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import openpyxl
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            text_parts = []
            for sheet in workbook.worksheets:
                text_parts.append(f"Sheet: {sheet.title}")
                for row in sheet.iter_rows(values_only=True):
                    row_values = ["" if cell is None else str(cell) for cell in row]
                    row_text = "\t".join(row_values).strip()
                    if row_text:
                        text_parts.append(row_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("openpyxl not installed, skipping XLSX processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading XLSX file {file_path}: {str(e)}")
            return ""

class RTFProcessor:
    """Processor for RTF files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            from striprtf.striprtf import rtf_to_text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return rtf_to_text(f.read())
        except ImportError:
            logger.warning("striprtf not installed, skipping RTF processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading RTF file {file_path}: {str(e)}")
            return ""

class ODTProcessor:
    """Processor for ODT files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            from odf import text as odf_text
            from odf import teletype
            from odf.opendocument import load
            doc = load(str(file_path))
            paragraphs = doc.getElementsByType(odf_text.P)
            text_parts = []
            for paragraph in paragraphs:
                paragraph_text = teletype.extractText(paragraph).strip()
                if paragraph_text:
                    text_parts.append(paragraph_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("odfpy not installed, skipping ODT processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading ODT file {file_path}: {str(e)}")
            return ""

class PPTXProcessor:
    """Processor for PPTX files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import pptx
            prs = pptx.Presentation(file_path)
            text_parts = []
            for slide in prs.slides:
                # Slide shapes text
                for shape in slide.shapes:
                    self._extract_shape_text(shape, text_parts)

                # Speaker notes
                try:
                    notes_slide = slide.notes_slide
                    if notes_slide and notes_slide.notes_text_frame:
                        notes_text = notes_slide.notes_text_frame.text
                        if notes_text:
                            text_parts.append(notes_text)
                except Exception:
                    pass

            if text_parts:
                return "\n".join(text_parts)

            # Fallback: extract text directly from PPTX XML
            xml_text = self._extract_text_from_pptx_xml(file_path)
            return xml_text
        except ImportError:
            logger.warning("python-pptx not installed, skipping PPTX processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading PPTX file {file_path}: {str(e)}")
            return ""

    def _extract_shape_text(self, shape, text_parts):
        """Recursively extract text from shapes, including grouped shapes and tables."""
        try:
            # Grouped shapes
            if hasattr(shape, "shapes"):
                for sub_shape in shape.shapes:
                    self._extract_shape_text(sub_shape, text_parts)

            # Text frames
            if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                text = shape.text_frame.text
                if text:
                    text_parts.append(text)
                else:
                    for paragraph in shape.text_frame.paragraphs:
                        paragraph_text = "".join(run.text for run in paragraph.runs).strip()
                        if paragraph_text:
                            text_parts.append(paragraph_text)

            # Tables
            if hasattr(shape, "has_table") and shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text:
                            text_parts.append(cell.text)
        except Exception:
            return

    def _extract_text_from_pptx_xml(self, file_path: Path) -> str:
        """Extract text runs from PPTX XML as a fallback."""
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            text_parts = []
            with zipfile.ZipFile(file_path, "r") as zf:
                slide_files = [name for name in zf.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
                notes_files = [name for name in zf.namelist() if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")]

                for name in slide_files + notes_files:
                    try:
                        xml_data = zf.read(name)
                        root = ET.fromstring(xml_data)
                        for node in root.iter():
                            if node.tag.endswith("}t") and node.text:
                                text = node.text.strip()
                                if text:
                                    text_parts.append(text)
                    except Exception:
                        continue

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting PPTX XML text {file_path}: {str(e)}")
            return ""

class ImageProcessor:
    """Processor for image files using Gemini LLM for captioning"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava:latest")
        logger.info("ImageProcessor initialized")

    async def extract_text(self, file_path: Path) -> str:
        """Extract text content from an image file using Gemini LLM for detailed captioning"""
        try:
            from PIL import Image

            # Open the image
            raw_image = Image.open(file_path).convert('RGB')

            # Extract basic metadata
            metadata = self._extract_image_metadata(file_path)

            # Build a structured prompt for LLaVA
            prompt = (
                "Analyze the image and return JSON with these fields:\n"
                "caption (1-2 sentences), objects (array), people_count (number), "
                "clothing (array), colors (array), scene (string), activity (string), "
                "context (string). Return ONLY valid JSON."
            )

            analysis = await self._generate_vision_analysis(raw_image, prompt)
            caption = analysis.get("caption") or f"Image file {file_path.name}"

            # Normalize tags for easier display
            tags = self._build_tags(analysis)
            metadata["analysis"] = analysis
            metadata["tags"] = tags

            # Return structured data as JSON string
            return json.dumps({
                "caption": caption,
                "analysis": analysis,
                "metadata": metadata
            })

        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {str(e)}")
            return json.dumps({
                "caption": f"Error processing image: {str(e)}",
                "metadata": self._extract_image_metadata(file_path)
            })

    def _extract_image_metadata(self, file_path: Path) -> Dict:
        """Extract basic metadata from image file"""
        try:
            from PIL import Image
            import piexif

            with Image.open(file_path) as img:
                stat = os.stat(file_path)
                metadata = {
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                    "file_size": os.path.getsize(file_path),
                    "file_name": os.path.basename(file_path),
                    "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "exif": {}
                }

                try:
                    exif_dict = piexif.load(str(file_path))
                    exif = {}

                    date_taken = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
                    if date_taken:
                        try:
                            exif["date_taken"] = datetime.strptime(date_taken.decode("utf-8"), "%Y:%m:%d %H:%M:%S").date().isoformat()
                        except Exception:
                            exif["date_taken"] = None

                    camera_model = exif_dict.get("0th", {}).get(piexif.ImageIFD.Model)
                    if camera_model:
                        exif["camera_model"] = camera_model.decode("utf-8", errors="ignore")

                    orientation = exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation)
                    if orientation:
                        exif["orientation"] = int(orientation)

                    gps_info = exif_dict.get("GPS", {})
                    exif["gps"] = self._parse_gps(gps_info)

                    metadata["exif"] = exif
                except Exception as exif_error:
                    logger.debug(f"No EXIF data for {file_path}: {exif_error}")

                return metadata
        except Exception as e:
            logger.error(f"Error extracting image metadata {file_path}: {str(e)}")
            return {
                "format": "",
                "size": "",
                "mode": "",
                "file_size": os.path.getsize(file_path),
                "file_name": os.path.basename(file_path),
                "created_at": None,
                "modified_at": None,
                "exif": {}
            }

    async def get_image_embedding(self, file_path: Path) -> Dict:
        """Generate text embedding for the image caption"""
        try:
            from services.embedding_service import EmbeddingService
            import numpy as np

            # Get the caption and analysis from the image
            caption_data = json.loads(await self.extract_text(file_path))
            caption = caption_data.get("caption", "")
            analysis = caption_data.get("analysis", {})
            metadata = caption_data.get("metadata", {})

            if not caption:
                caption = f"Image file {file_path.name}"

            search_text = self._build_search_text(caption, analysis, metadata)

            # Generate text embedding for the caption using the embedding service
            embedding_service = EmbeddingService()
            text_embedding = await embedding_service.generate_embedding(f"image: {search_text}")

            # Convert to numpy array if it's not already
            if text_embedding is not None and not isinstance(text_embedding, np.ndarray):
                text_embedding = np.array(text_embedding)

            return {
                "image_embedding": None,  # We're not using image embeddings anymore
                "text_embedding": text_embedding,
                "caption": caption,
                "metadata": metadata,
                "analysis": analysis,
                "search_text": search_text
            }

        except Exception as e:
            logger.error(f"Error generating text embedding for image {file_path}: {str(e)}")
            return {
                "image_embedding": None,
                "text_embedding": None,
                "caption": ""
            }

    async def _generate_vision_analysis(self, image, prompt: str) -> Dict:
        try:
            import httpx

            resized = self._resize_image(image)
            image_b64 = self._encode_image(resized)

            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.ollama_base_url}/api/generate", json=payload)

            if response.status_code != 200:
                logger.error(f"Ollama vision request failed: {response.status_code} - {response.text}")
                return {}

            response_json = response.json()
            raw_text = response_json.get("response", "")
            parsed = self._parse_json_from_text(raw_text)

            if not parsed:
                logger.warning("Ollama response did not contain valid JSON")
                return {}

            return parsed
        except Exception as e:
            logger.error(f"Error calling Ollama vision model: {e}")
            return {}

    def _resize_image(self, image, max_dim: int = 512):
        if max(image.size) <= max_dim:
            return image

        resized = image.copy()
        resized.thumbnail((max_dim, max_dim))
        return resized

    def _encode_image(self, image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _parse_json_from_text(self, text: str) -> Dict:
        if not text:
            return {}

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}

        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return {}

    def _build_tags(self, analysis: Dict) -> list:
        tags = []
        for key in ("objects", "clothing", "colors"):
            values = analysis.get(key) or []
            if isinstance(values, list):
                tags.extend([str(v).strip() for v in values if str(v).strip()])

        for key in ("scene", "activity", "context"):
            value = analysis.get(key)
            if value:
                tags.append(str(value).strip())

        deduped = []
        seen = set()
        for tag in tags:
            lowered = tag.lower()
            if lowered and lowered not in seen:
                seen.add(lowered)
                deduped.append(tag)
        return deduped

    def _build_search_text(self, caption: str, analysis: Dict, metadata: Dict) -> str:
        parts = [caption]

        date_hint = metadata.get("exif", {}).get("date_taken") or metadata.get("created_at")
        if date_hint:
            parts.append(f"Taken around {date_hint}.")

        objects = analysis.get("objects") or []
        if objects:
            parts.append("Objects: " + ", ".join(objects))

        scene = analysis.get("scene")
        if scene:
            parts.append(f"Scene: {scene}.")

        activity = analysis.get("activity")
        if activity:
            parts.append(f"Activity: {activity}.")

        colors = analysis.get("colors") or []
        if colors:
            parts.append("Colors: " + ", ".join(colors))

        clothing = analysis.get("clothing") or []
        if clothing:
            parts.append("Clothing: " + ", ".join(clothing))

        return " ".join(parts).strip()

    def _parse_gps(self, gps_info: Dict) -> Dict:
        try:
            import piexif

            def _rational_to_float(value):
                if isinstance(value, tuple) and len(value) == 2 and value[1] != 0:
                    return value[0] / value[1]
                return None

            def _convert_to_degrees(values):
                degrees = _rational_to_float(values[0])
                minutes = _rational_to_float(values[1])
                seconds = _rational_to_float(values[2])
                if degrees is None or minutes is None or seconds is None:
                    return None
                return degrees + (minutes / 60.0) + (seconds / 3600.0)

            gps_latitude = gps_info.get(piexif.GPSIFD.GPSLatitude)
            gps_latitude_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef)
            gps_longitude = gps_info.get(piexif.GPSIFD.GPSLongitude)
            gps_longitude_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef)

            if not (gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref):
                return {}

            lat = _convert_to_degrees(gps_latitude)
            lon = _convert_to_degrees(gps_longitude)
            if lat is None or lon is None:
                return {}

            if gps_latitude_ref.decode("utf-8", errors="ignore") != "N":
                lat = -lat
            if gps_longitude_ref.decode("utf-8", errors="ignore") != "E":
                lon = -lon

            return {"lat": lat, "lon": lon}
        except Exception:
            return {}

class FileProcessorFactory:
    """Factory for creating file processors"""

    _processors = {
        '.txt': TextFileProcessor(),
        '.md': TextFileProcessor(),
        '.py': TextFileProcessor(),
        '.js': TextFileProcessor(),
        '.html': TextFileProcessor(),
        '.css': TextFileProcessor(),
        '.json': TextFileProcessor(),
        '.xml': TextFileProcessor(),
        '.yml': TextFileProcessor(),
        '.yaml': TextFileProcessor(),
        '.pdf': PDFProcessor(),
        '.docx': DocxProcessor(),
        '.doc': DocxProcessor(),
        '.csv': CSVProcessor(),
        '.tsv': CSVProcessor(),
        '.xlsx': XLSXProcessor(),
        '.rtf': RTFProcessor(),
        '.odt': ODTProcessor(),
        '.pptx': PPTXProcessor(),
    }

    _image_processor = None

    @classmethod
    def initialize(cls, llm_client=None):
        """Initialize the factory with an LLM client for image processing"""
        if llm_client:
            cls._image_processor = ImageProcessor(llm_client=llm_client)
        else:
            cls._image_processor = ImageProcessor()

    @classmethod
    def get_processor(cls, file_extension: str) -> FileProcessor:
        """Get appropriate processor for file extension"""
        # Handle image extensions
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif']
        if file_extension.lower() in image_extensions:
            if cls._image_processor is None:
                cls._image_processor = ImageProcessor()
            return cls._image_processor

        # Default to text processor for other extensions
        processor = cls._processors.get(file_extension.lower())
        if processor is None:
            return cls._processors['.txt']
        return processor
