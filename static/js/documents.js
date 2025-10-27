// StudyMate AI - Document Management

let uploadedDocuments = [];
let isUploading = false;

// Load documents from server
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents?user_id=web_user');
        if (response.ok) {
            uploadedDocuments = await response.json();
            renderDocuments();
            updateDocumentCount();
        } else {
            console.warn('Failed to load documents:', response.status);
            uploadedDocuments = [];
            renderDocuments();
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        uploadedDocuments = [];
        renderDocuments();
    }
}

// Setup file upload
function setupFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    if (!dropZone || !fileInput) {
        console.warn('Drop zone or file input not found');
        return;
    }
    
    // Click to upload
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
            // Reset file input
            e.target.value = '';
        }
    });
    
    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('drag-over');
        }
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });
    
    console.log('✅ File upload setup complete');
}

// Handle file uploads
async function handleFiles(files) {
    if (isUploading) {
        showNotification('Upload already in progress', 'warning');
        return;
    }
    
    const validFiles = Array.from(files).filter(file => {
        const validTypes = ['.pdf', '.docx', '.pptx', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const isValidType = validTypes.includes(fileExtension);
        const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB limit
        
        if (!isValidType) {
            showNotification(`Invalid file type: ${file.name}. Supported: PDF, DOCX, PPTX, TXT`, 'error');
        } else if (!isValidSize) {
            showNotification(`File too large: ${file.name}. Max size: 50MB`, 'error');
        }
        
        return isValidType && isValidSize;
    });
    
    if (validFiles.length === 0) {
        return;
    }
    
    console.log(`📁 Processing ${validFiles.length} files...`);
    
    // Close drop zone
    if (window.closeDropZone) {
        window.closeDropZone();
    }
    
    for (const file of validFiles) {
        await uploadFile(file);
    }
}

// Upload single file
async function uploadFile(file) {
    isUploading = true;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 'web_user');
    formData.append('session_id', window.currentSessionId || window.currentSession || 'default');
    
    // Show upload progress
    const uploadItem = createUploadProgressItem(file);
    const documentsList = document.getElementById('documentsList');
    
    // Remove empty state if it exists
    const emptyState = documentsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    documentsList.appendChild(uploadItem);
    
    try {
        console.log(`📤 Uploading ${file.name}...`);
        
        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Remove progress item
            uploadItem.remove();
            
            // Add to documents list
            uploadedDocuments.push(result);
            renderDocuments();
            
            showNotification(`✅ Successfully uploaded ${file.name}`, 'success');
            console.log(`✅ Upload complete: ${file.name}`);
        } else {
            const errorText = await response.text();
            let errorMessage = 'Upload failed';
            
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.detail || errorMessage;
            } catch {
                errorMessage = errorText || errorMessage;
            }
            
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Upload error:', error);
        uploadItem.remove();
        showNotification(`❌ Failed to upload ${file.name}: ${error.message}`, 'error');
        
        // Show empty state again if no documents
        if (uploadedDocuments.length === 0) {
            renderDocuments();
        }
    } finally {
        isUploading = false;
    }
}

// Create upload progress item
function createUploadProgressItem(file) {
    const item = document.createElement('div');
    item.className = 'document-item uploading';
    item.innerHTML = `
        <div class="document-icon">
            <i class="fas fa-file-upload"></i>
        </div>
        <div class="document-info">
            <div class="document-name">${file.name}</div>
            <div class="document-meta">
                <span class="document-size">${formatFileSize(file.size)}</span>
                <span class="upload-status">Uploading...</span>
            </div>
            <div class="upload-progress">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        </div>
    `;
    return item;
}

// Render documents list
function renderDocuments() {
    const documentsList = document.getElementById('documentsList');
    
    if (uploadedDocuments.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <p>No documents uploaded yet</p>
                <p class="text-muted">Upload PDFs, Word docs, PowerPoints, or text files to chat with your content</p>
            </div>
        `;
        return;
    }
    
    documentsList.innerHTML = uploadedDocuments.map(doc => `
        <div class="document-item" data-doc-id="${doc.id}">
            <div class="document-icon">
                <i class="fas ${getFileIcon(doc.filename)}"></i>
            </div>
            <div class="document-info">
                <div class="document-name" title="${doc.filename}">${doc.filename}</div>
                <div class="document-meta">
                    <span class="document-size">${formatFileSize(doc.file_size)}</span>
                    <span class="document-date">${formatUploadDate(doc.upload_date)}</span>
                    <span class="document-status ${doc.status}">${doc.status}</span>
                </div>
                ${doc.chunk_count ? `<div class="document-chunks">${doc.chunk_count} chunks processed</div>` : ''}
            </div>
            <div class="document-actions">
                <button class="document-action" onclick="viewDocument('${doc.id}')" title="View">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="document-action" onclick="downloadDocument('${doc.id}')" title="Download">
                    <i class="fas fa-download"></i>
                </button>
                <button class="document-action" onclick="deleteDocument('${doc.id}')" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    // Update document count
    updateDocumentCount();
}

// Get file icon based on extension
function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': 'fa-file-pdf',
        'docx': 'fa-file-word',
        'doc': 'fa-file-word',
        'pptx': 'fa-file-powerpoint',
        'ppt': 'fa-file-powerpoint',
        'txt': 'fa-file-alt',
        'md': 'fa-file-alt'
    };
    return icons[extension] || 'fa-file';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format upload date
function formatUploadDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

// View document
async function viewDocument(docId) {
    try {
        const response = await fetch(`/api/documents/${docId}/content`);
        if (response.ok) {
            const content = await response.json();
            showDocumentModal(content);
        }
    } catch (error) {
        console.error('Error viewing document:', error);
        showNotification('Failed to load document content', 'error');
    }
}

// Download document
async function downloadDocument(docId) {
    try {
        const response = await fetch(`/api/documents/${docId}/download`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition').split('filename=')[1];
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    } catch (error) {
        console.error('Error downloading document:', error);
        showNotification('Failed to download document', 'error');
    }
}

// Delete document
async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
        const response = await fetch(`/api/documents/${docId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            uploadedDocuments = uploadedDocuments.filter(doc => doc.id !== docId);
            renderDocuments();
            showNotification('Document deleted successfully', 'success');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showNotification('Failed to delete document', 'error');
    }
}

// Show document modal
function showDocumentModal(content) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content document-modal">
            <div class="modal-header">
                <h3>${content.filename}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="document-content">
                    ${content.content.replace(/\n/g, '<br>')}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                    Close
                </button>
                <button class="btn btn-primary" onclick="askAboutDocument('${content.id}')">
                    Ask About This Document
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Ask about document
function askAboutDocument(docId) {
    const doc = uploadedDocuments.find(d => d.id === docId);
    if (doc) {
        const message = `Tell me about the document "${doc.filename}"`;
        document.getElementById('messageInput').value = message;
        
        // Close modal
        document.querySelector('.modal-overlay')?.remove();
        
        // Send message
        sendMessage();
    }
}

// Update document count
function updateDocumentCount() {
    const countElement = document.getElementById('documentCount');
    if (countElement) {
        countElement.textContent = uploadedDocuments.length;
    }
}

// Search documents
function searchDocuments(query) {
    const filteredDocs = uploadedDocuments.filter(doc => 
        doc.filename.toLowerCase().includes(query.toLowerCase())
    );
    
    const documentsList = document.getElementById('documentsList');
    
    if (filteredDocs.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No documents found for "${query}"</p>
            </div>
        `;
        return;
    }
    
    // Render filtered documents
    const originalDocs = uploadedDocuments;
    uploadedDocuments = filteredDocs;
    renderDocuments();
    uploadedDocuments = originalDocs;
}

// Clear all documents
async function clearAllDocuments() {
    if (!confirm('Are you sure you want to delete all documents? This action cannot be undone.')) return;
    
    try {
        const response = await fetch('/api/documents/clear', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            uploadedDocuments = [];
            renderDocuments();
            showNotification('All documents cleared successfully', 'success');
        }
    } catch (error) {
        console.error('Error clearing documents:', error);
        showNotification('Failed to clear documents', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to notifications container or create one
    let container = document.getElementById('notificationsContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationsContainer';
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Bulk document operations
function selectAllDocuments() {
    document.querySelectorAll('.document-item').forEach(item => {
        item.classList.add('selected');
    });
    updateBulkActions();
}

function deselectAllDocuments() {
    document.querySelectorAll('.document-item').forEach(item => {
        item.classList.remove('selected');
    });
    updateBulkActions();
}

function updateBulkActions() {
    const selectedCount = document.querySelectorAll('.document-item.selected').length;
    const bulkActions = document.getElementById('bulkActions');
    
    if (bulkActions) {
        bulkActions.style.display = selectedCount > 0 ? 'flex' : 'none';
        bulkActions.querySelector('.selected-count').textContent = `${selectedCount} selected`;
    }
}

// Initialize document management
document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload();
    loadDocuments();
});