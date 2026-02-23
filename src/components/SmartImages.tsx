import React, { useState, useEffect, KeyboardEvent } from 'react';
import { ApiService } from '../services/api';
import { Plus, Folder, RefreshCw, Image as ImageIcon, ExternalLink, FolderOpen, X } from 'lucide-react';
import FolderPicker from './FolderPicker';
import './SmartImages.css';

interface Image {
  id: number;
  file_path?: string;
  file_name: string;
  caption: string;
  file_size: number | string;
  date_created: string;
  date_indexed: string;
  date_modified?: string;
  format: string;
  file_type?: string;
  resolution: string;
  tags: string[];
  folder_path?: string;
  date_taken?: string | null;
  camera_model?: string | null;
  gps?: { lat?: number; lon?: number } | null;
}

interface IndexedFolder {
  id: number;
  path: string;
  name: string;
  file_count: number;
  last_indexed: string;
}

const SmartImages: React.FC = () => {
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [newName, setNewName] = useState('');
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [indexedFolders, setIndexedFolders] = useState<IndexedFolder[]>([]);
  const [expandedCaptions, setExpandedCaptions] = useState<Set<number>>(new Set());
  const [activeImage, setActiveImage] = useState<Image | null>(null);

  useEffect(() => {
    loadImages();
    loadFolders();
  }, []);

  const loadImages = async () => {
    try {
      setLoading(true);
      const fetchedImages = await ApiService.getIndexedImages();
      setImages(fetchedImages);
    } catch (error) {
      console.error('Error fetching images:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFolders = async () => {
    try {
      const folders = await ApiService.getFolders();
      setIndexedFolders(folders || []);
    } catch (error) {
      console.error('Error fetching folders:', error);
    }
  };

  const formatBytes = (value: number | string) => {
    const bytes = typeof value === 'string' ? Number(value) : value;
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 MB';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(mb >= 10 ? 1 : 2)} MB`;
  };

  const handleAddFolders = () => {
    setShowFolderPicker(true);
  };

  const handleFoldersSelected = async (selectedPaths: string[]) => {
    setShowFolderPicker(false);
    if (selectedPaths.length > 0) {
      setIndexing(true);
      try {
        await ApiService.indexFolders({
          folder_paths: selectedPaths,
        });
        // Poll for completion
        const checkStatus = async () => {
          const status = await ApiService.getIndexStatus();
          if (!status.is_indexing) {
            loadImages();
            loadFolders();
            setIndexing(false);
          } else {
            setTimeout(checkStatus, 1000);
          }
        };
        checkStatus();
      } catch (error) {
        console.error('Error indexing folders:', error);
        setIndexing(false);
      }
    }
  };

  const handleSearch = async () => {
    try {
      if (!searchQuery.trim()) {
        loadImages();
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
      if (!newName.trim()) return;
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

  const openFile = async (filePath?: string) => {
    if (!filePath) return;
    if (window.electronAPI) {
      try {
        const result = await window.electronAPI.openFile(filePath);
        if (!result.success) {
          alert(`Failed to open file: ${result.error}`);
        }
      } catch (error) {
        console.error('Error opening file:', error);
        alert('Failed to open file');
      }
    } else {
      alert('File opening is only available in the desktop app');
    }
  };

  const showInFolder = async (filePath?: string) => {
    if (!filePath) return;
    if (window.electronAPI) {
      try {
        const result = await window.electronAPI.showFileInFolder(filePath);
        if (!result.success) {
          alert(`Failed to show file in folder: ${result.error}`);
        }
      } catch (error) {
        console.error('Error showing file in folder:', error);
        alert('Failed to show file in folder');
      }
    } else {
      alert('This feature is only available in the desktop app');
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    const confirmDelete = window.confirm('Remove this image from the index?');
    if (!confirmDelete) return;
    try {
      await ApiService.deleteImage(imageId);
      setImages(images.filter(image => image.id !== imageId));
    } catch (error) {
      console.error('Error deleting image:', error);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    const confirmDelete = window.confirm('Remove this folder and its files from the index?');
    if (!confirmDelete) return;
    try {
      await ApiService.removeFolder(folderId);
      setIndexedFolders(indexedFolders.filter(folder => folder.id !== folderId));
      loadImages();
    } catch (error) {
      console.error('Error deleting folder:', error);
    }
  };

  const toggleCaption = (imageId: number) => {
    setExpandedCaptions((prev) => {
      const next = new Set(prev);
      if (next.has(imageId)) {
        next.delete(imageId);
      } else {
        next.add(imageId);
      }
      return next;
    });
  };

  if (loading) {
    return (
      <div className="smart-images-container">
        <div className="loading-state">
          <RefreshCw className="spinning" size={24} />
          <p>Loading images...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="smart-images-container">
      <div className="smart-images-header">
        <div className="header-content">
          <h1 className="gradient-text">Smart Images</h1>
          <p className="subtitle">Search images semantically with AI understanding</p>
        </div>
      </div>

      {/* Action Bar */}
      <div className="smart-images-actions">
        <button 
          className="add-folder-btn gradient-bg-blue" 
          onClick={handleAddFolders}
          disabled={indexing}
        >
          <Plus size={20} />
          {indexing ? 'Indexing...' : 'Add Folders'}
        </button>
        <button 
          className="refresh-btn" 
          onClick={loadImages}
          disabled={loading || indexing}
        >
          <RefreshCw size={20} />
        </button>
      </div>

      {/* Search Box */}
      <div className="search-box-modern">
        <input
          type="text"
          aria-label="Search images"
          placeholder="Search images using semantic meaning"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button onClick={handleSearch} className="search-button">Search</button>
      </div>

      {/* Indexed Folders */}
      {indexedFolders.length > 0 && (
        <div className="indexed-folders">
          <h2>Indexed Folders</h2>
          <div className="folder-list">
            {indexedFolders.map((folder) => (
              <div key={folder.id} className="folder-item">
                <div className="folder-info">
                  <Folder size={16} />
                  <div className="folder-text">
                    <div className="folder-name" title={folder.path}>{folder.name}</div>
                    <div className="folder-meta">{folder.file_count} files</div>
                  </div>
                </div>
                <button
                  className="folder-delete-btn"
                  onClick={() => handleDeleteFolder(folder.id)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Image Grid */}
      <div className="image-grid">
        {images.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <ImageIcon size={64} />
            </div>
            <h3>No Images Found</h3>
            <p>Add folders containing images to get started with AI-powered image search.</p>
            <button 
              className="cta-button gradient-bg-blue" 
              onClick={handleAddFolders}
            >
              <Plus size={20} />
              Add Your First Folder
            </button>
          </div>
        ) : (
          images.map((image) => (
            <div
              key={image.id}
              className="image-card hover-lift"
              role="button"
              tabIndex={0}
              onClick={() => setActiveImage(image)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') setActiveImage(image);
              }}
            >
              <div className="image-wrapper">
                <img
                  src={ApiService.getImageContentUrl(image.id)}
                  alt={image.file_name}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not available%3C/text%3E%3C/svg%3E';
                  }}
                />
              </div>
              <div className="image-info">
                <h4 title={image.file_name}>{image.file_name}</h4>
                <p className={`caption ${expandedCaptions.has(image.id) ? 'expanded' : ''}`}>
                  {image.caption}
                </p>
                {image.caption && image.caption.length > 120 && (
                  <button
                    className="caption-toggle"
                    onClick={(event) => {
                      event.stopPropagation();
                      toggleCaption(image.id);
                    }}
                  >
                    {expandedCaptions.has(image.id) ? 'Show less' : 'Show more'}
                  </button>
                )}
                
                {/* Tags */}
                {image.tags && image.tags.length > 0 && (
                  <div className="tags">
                    {image.tags.slice(0, 5).map((tag, index) => (
                      <span key={`${image.id}-tag-${index}`} className="tag">{tag}</span>
                    ))}
                    {image.tags.length > 5 && <span className="tag-more">+{image.tags.length - 5}</span>}
                  </div>
                )}
                
                <div className="image-meta">
                  <span className="meta-item">
                    <strong>Format:</strong> {image.format || image.file_type || 'unknown'}
                  </span>
                  <span className="meta-item">
                    <strong>Size:</strong> {formatBytes(image.file_size)}
                  </span>
                  <span className="meta-item">
                    <strong>Resolution:</strong> {image.resolution || 'unknown'}
                  </span>
                  {image.date_modified && (
                    <span className="meta-item">
                      <strong>Modified:</strong> {new Date(image.date_modified).toLocaleDateString()}
                    </span>
                  )}
                  {image.date_taken && (
                    <span className="meta-item">
                      <strong>Date:</strong> {image.date_taken}
                    </span>
                  )}
                  {image.camera_model && (
                    <span className="meta-item">
                      <strong>Camera:</strong> {image.camera_model}
                    </span>
                  )}
                  {image.gps && (image.gps.lat || image.gps.lon) && (
                    <span className="meta-item">
                      <strong>GPS:</strong> {image.gps.lat?.toFixed(5)}, {image.gps.lon?.toFixed(5)}
                    </span>
                  )}
                  {image.folder_path && (
                    <span className="meta-item folder" title={image.folder_path}>
                      <Folder size={14} />
                      {image.folder_path.split(/[\\/]/).pop()}
                    </span>
                  )}
                </div>

                <div className="image-path-row">
                  <span className="image-path" title={image.file_path}>{image.file_path}</span>
                  <div className="image-actions">
                    <button
                      className="icon-btn"
                      onClick={(event) => {
                        event.stopPropagation();
                        showInFolder(image.file_path);
                      }}
                      title="Show in folder"
                    >
                      <FolderOpen size={16} />
                    </button>
                    <button
                      className="icon-btn"
                      onClick={(event) => {
                        event.stopPropagation();
                        openFile(image.file_path);
                      }}
                      title="Open file"
                    >
                      <ExternalLink size={16} />
                    </button>
                  </div>
                </div>

                <button
                  className="rename-btn"
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelectedImageId(image.id);
                    setNewName(image.file_name);
                  }}
                >
                  Rename
                </button>
                <button
                  className="delete-btn"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleDeleteImage(image.id);
                  }}
                >
                  Remove from Index
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {activeImage && (
        <div className="image-preview-overlay" onClick={() => setActiveImage(null)}>
          <div className="image-preview-modal" onClick={(event) => event.stopPropagation()}>
            <div className="image-preview-header">
              <div>
                <h2>{activeImage.file_name}</h2>
                <p>{activeImage.caption}</p>
              </div>
              <button className="image-preview-close" onClick={() => setActiveImage(null)}>
                <X size={18} />
              </button>
            </div>
            <div className="image-preview-body">
              <div className="image-preview-image">
                <img src={ApiService.getImageContentUrl(activeImage.id)} alt={activeImage.file_name} />
              </div>
              <div className="image-preview-details">
                {activeImage.tags && activeImage.tags.length > 0 && (
                  <div className="image-preview-tags">
                    {activeImage.tags.map((tag, index) => (
                      <span key={`${activeImage.id}-full-tag-${index}`} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                <div className="image-preview-meta">
                  <span><strong>Format:</strong> {activeImage.format || activeImage.file_type || 'unknown'}</span>
                  <span><strong>Size:</strong> {formatBytes(activeImage.file_size)}</span>
                  <span><strong>Resolution:</strong> {activeImage.resolution || 'unknown'}</span>
                  {activeImage.date_modified && <span><strong>Modified:</strong> {new Date(activeImage.date_modified).toLocaleDateString()}</span>}
                  {activeImage.date_taken && <span><strong>Date:</strong> {activeImage.date_taken}</span>}
                  {activeImage.camera_model && <span><strong>Camera:</strong> {activeImage.camera_model}</span>}
                  {activeImage.gps && (activeImage.gps.lat || activeImage.gps.lon) && (
                    <span><strong>GPS:</strong> {activeImage.gps.lat?.toFixed(5)}, {activeImage.gps.lon?.toFixed(5)}</span>
                  )}
                  {activeImage.folder_path && (
                    <span><strong>Folder:</strong> {activeImage.folder_path}</span>
                  )}
                  {activeImage.file_path && (
                    <span><strong>Path:</strong> {activeImage.file_path}</span>
                  )}
                </div>
                <div className="image-preview-actions">
                  <button onClick={() => showInFolder(activeImage.file_path)}>
                    <FolderOpen size={16} />
                    Show in Folder
                  </button>
                  <button onClick={() => openFile(activeImage.file_path)}>
                    <ExternalLink size={16} />
                    Open File
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {selectedImageId !== null && (
        <div className="modal-overlay" onClick={() => setSelectedImageId(null)}>
          <div
            className="rename-modal"
            onClick={(e) => e.stopPropagation()}
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
                if (e.key === 'Escape') setSelectedImageId(null);
              }}
              autoFocus
              placeholder="Enter new filename"
            />
            <div className="modal-buttons">
              <button className="btn-save" onClick={() => handleRename(selectedImageId)}>Save</button>
              <button className="btn-cancel" onClick={() => setSelectedImageId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Folder Picker */}
      {showFolderPicker && (
        <FolderPicker
          onSelect={handleFoldersSelected}
          onCancel={() => setShowFolderPicker(false)}
        />
      )}
    </div>
  );
};

export default SmartImages;
