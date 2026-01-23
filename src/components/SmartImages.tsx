import React, { useState, useEffect, KeyboardEvent } from 'react';
import { ApiService } from '../services/api';
import './SmartImages.css';

interface Image {
  id: number;
  file_name: string;
  caption: string;
  file_size: string;
  date_created: string;
  date_indexed: string;
  format: string;
  resolution: string;
  tags: string[];
}

const SmartImages: React.FC = () => {
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    const fetchImages = async () => {
      try {
        const fetchedImages = await ApiService.getIndexedImages();
        setImages(fetchedImages);
      } catch (error) {
        console.error('Error fetching images:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchImages();
  }, []);

  const handleSearch = async () => {
    try {
      if (!searchQuery.trim()) {
        // If search query is empty, refetch all images
        const fetchedImages = await ApiService.getIndexedImages();
        setImages(fetchedImages);
        return;
      }
      const searchedImages = await ApiService.searchImages(searchQuery);
      setImages(searchedImages);
    } catch (error) {
      console.error('Error searching images:', error);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleRename = async (imageId: number) => {
    try {
      if (!newName.trim()) return; // Avoid empty name
      await ApiService.renameImage(imageId, newName);
      const updatedImages = images.map(image =>
        image.id === imageId ? { ...image, file_name: newName } : image
      );
      setImages(updatedImages);
      setSelectedImageId(null);
    } catch (error) {
      console.error('Error renaming image:', error);
    }
  };

  if (loading) {
    return <div>Loading images...</div>;
  }

  return (
    <div className="smart-images-container">
      <h1>Smart Images</h1>

      {/* Search Box */}
      <div className="search-box">
        <input
          type="text"
          aria-label="Search images"
          placeholder="Search images..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button onClick={handleSearch}>Search</button>
      </div>

      {/* Image Grid */}
      <div className="image-grid">
        {images.length === 0 ? (
          <div className="empty-state">
            <p>No images found. Try a different search query or check if any images are indexed.</p>
          </div>
        ) : (
          images.map((image) => (
            <div key={image.id} className="image-card">
              <img
                src={`/api/images/${image.id}/content`}
                alt={image.file_name}
                onError={(e) => {
                  console.error(`Error loading image: ${image.file_name}`);
                  (e.target as HTMLImageElement).src = '/placeholder.jpg';
                }}
              />
              <div className="image-info">
                <p><strong>{image.file_name}</strong></p>
                <p>{image.caption}</p>
                <p><strong>Resolution:</strong> {image.resolution}</p>
                <p><strong>Size:</strong> {image.file_size}</p>
                <p><strong>Created:</strong> {new Date(image.date_created).toLocaleDateString()}</p>

                {/* Tags */}
                <div className="tags">
                  {image.tags.map((tag, index) => (
                    <span key={`${image.id}-${tag}-${index}`} className="tag">{tag}</span>
                  ))}
                </div>

                <button
                  onClick={() => {
                    setSelectedImageId(image.id);
                    setNewName(image.file_name);
                  }}
                >
                  Rename
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Rename Modal */}
      {selectedImageId !== null && (
        <div
          className="rename-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="rename-modal-title"
        >
          <h2 id="rename-modal-title">Rename Image</h2>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') handleRename(selectedImageId);
            }}
            autoFocus
          />
          <div className="modal-buttons">
            <button onClick={() => handleRename(selectedImageId)}>Save</button>
            <button onClick={() => setSelectedImageId(null)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartImages;
