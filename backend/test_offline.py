from services.file_processors import ImageProcessor
from services.vector_store import VectorStore, DateTimeEncoder
import json
from datetime import datetime

# Test datetime serialization
print("Testing datetime serialization...")
test_data = {"timestamp": datetime.now()}
try:
    json_str = json.dumps(test_data, cls=DateTimeEncoder)
    print("✓ Datetime serialization works correctly")
except Exception as e:
    print(f"✗ Datetime serialization failed: {e}")

# Test model loading
print("\nTesting model loading in offline mode...")
try:
    processor = ImageProcessor()
    print("✓ Models loaded successfully in offline mode")
except Exception as e:
    print(f"✗ Model loading failed: {e}")

# Test vector store
print("\nTesting vector store initialization...")
try:
    vector_store = VectorStore()
    print("✓ Vector store initialized successfully")
except Exception as e:
    print(f"✗ Vector store initialization failed: {e}")
