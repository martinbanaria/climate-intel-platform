import pytesseract
from PIL import Image
import io
import logging
from typing import Optional, Dict
import PyPDF2
import aiofiles

logger = logging.getLogger(__name__)

class OCRService:
    """OCR service for extracting text from images and PDFs"""
    
    def __init__(self):
        # Configure Tesseract if needed
        # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        pass
    
    async def extract_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return None
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF document"""
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            return '\n'.join(text_content)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    async def process_market_report(self, document_bytes: bytes, doc_type: str = "image") -> Dict:
        """Process market report document and extract structured data"""
        if doc_type == "image":
            text = await self.extract_text_from_image(document_bytes)
        else:
            # For PDF, save temporarily and process
            # This is simplified - in production, use proper temp file handling
            text = "PDF processing not implemented yet"
        
        if not text:
            return {"success": False, "error": "No text extracted"}
        
        # Parse extracted text to find price data
        market_data = self._parse_price_data(text)
        
        return {
            "success": True,
            "raw_text": text,
            "extracted_data": market_data
        }
    
    def _parse_price_data(self, text: str) -> Dict:
        """Parse price data from extracted text"""
        # Simple pattern matching for prices
        # In production, use more sophisticated NLP
        import re
        
        price_patterns = [
            r'(\w+)\s+₱?(\d+\.\d+)',  # Item ₱123.45
            r'(\w+):\s+₱?(\d+\.\d+)',  # Item: ₱123.45
        ]
        
        items = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                items.append({
                    'name': match[0].strip(),
                    'price': float(match[1])
                })
        
        return {'items': items, 'count': len(items)}

# Initialize OCR service
ocr_service = OCRService()
