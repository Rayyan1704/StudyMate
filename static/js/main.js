// StudyMate AI - Main Application Logic

// Global state
window.currentSession = null;
let currentMode = 'chat';
let isVoiceEnabled = false;
let isRecording = false;
let voiceOutputEnabled = true;
let websocket = null;
let isInitialized = false;

// Initialize the application
async function initializeApp() {
    if (isInitialized) return;
    
    console.log('🧠 Initializing StudyMate AI...');
    
    try {
        // Initialize body class for chat interface control
        document.body.classList.add('no-chat');
        
        // Hide typing indicator on initialization
        hideTypingIndicator();
        
        // Load user preferences
        loadUserPreferences();
        
        // Initialize WebSocket connection
        initializeWebSocket();
        
        // Load sessions
        await loadSessions();
        

        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize voice if available
        if (typeof initializeVoice === 'function') {
            initializeVoice();
        }
        
        // Update UI
        updateUI();
        
        isInitialized = true;
        console.log('✅ StudyMate AI initialized successfully!');
        
        // Hide loading overlay if it exists
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        
    } catch (error) {
        console.error('❌ Initialization error:', error);
        showNotification('Failed to initialize StudyMate AI', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Mode selector
    document.querySelectorAll('.mode-option').forEach(option => {
        option.addEventListener('click', () => {
            const mode = option.dataset.mode;
            switchMode(mode);
        });
    });
    
    // Message input
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            updateSendButton();
            adjustTextareaHeight(messageInput);
        });
        
        messageInput.addEventListener('keydown', handleKeyDown);
    }
    
    // Send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // File input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileInputChange);
    }
    
    // Setup chat drag and drop
    setupChatDragDrop();
    
    // Sidebar toggle for mobile
    document.addEventListener('click', (e) => {
        if (e.target.closest('.sidebar-toggle')) {
            toggleSidebar();
        }
    });
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar && !e.target.closest('.sidebar') && !e.target.closest('.sidebar-toggle')) {
                sidebar.classList.remove('open');
            }
        }
    });
}

// WebSocket connection
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/web_user`;
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('🔌 WebSocket connected');
            updateAIStatus('ready', 'AI Ready');
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('WebSocket message error:', error);
            }
        };
        
        websocket.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            updateAIStatus('warning', 'Connection Lost');
            // Attempt to reconnect after 3 seconds
            setTimeout(initializeWebSocket, 3000);
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateAIStatus('error', 'Connection Error');
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateAIStatus('error', 'Connection Failed');
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (data.type === 'response') {
        hideTypingIndicator();
        addMessage(data.content, 'assistant', data.source, data.metadata);
        
        // Text-to-speech if enabled
        if (voiceOutputEnabled && data.content) {
            speakText(data.content);
        }
    }
}

// Switch chat mode
function switchMode(mode, showMessage = true) {
    if (!mode || currentMode === mode) return; // Prevent duplicate calls
    
    // Check if there's an active chat session
    if (!window.currentSessionId && !window.currentSession) {
        showNotification('Please create a chat first before switching modes', 'warning');
        return;
    }
    
    const previousMode = currentMode;
    currentMode = mode;
    
    // Update UI
    document.querySelectorAll('.mode-option').forEach(option => {
        option.classList.toggle('active', option.dataset.mode === mode);
    });
    
    // Update header
    const sessionMode = document.getElementById('sessionMode');
    const modeIndicator = document.getElementById('modeIndicator');
    
    if (sessionMode) {
        sessionMode.textContent = `${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode`;
    }
    
    if (modeIndicator) {
        const modeIcons = {
            chat: 'fa-comments',
            tutor: 'fa-chalkboard-teacher',
            notes: 'fa-sticky-note',
            quiz: 'fa-question-circle'
        };
        
        modeIndicator.innerHTML = `
            <i class="fas ${modeIcons[mode] || 'fa-comments'}"></i>
            <span>${mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
        `;
    }
    
    // Update placeholder
    const placeholders = {
        chat: 'Ask me anything about your studies...',
        tutor: 'I\'ll explain this step by step. What would you like me to teach you?',
        notes: 'I\'ll create comprehensive notes from our conversation. What should I focus on?',
        quiz: 'I\'ll create a quiz based on what we\'ve discussed. Ready to test your knowledge?'
    };
    
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.placeholder = placeholders[mode] || placeholders.chat;
    }
    
    // Show mode activation message only when user manually switches and mode actually changed
    if (showMessage && previousMode !== mode) {
        const modeMessages = {
            chat: '💬 **Chat Mode Activated** - I\'m ready for general questions and discussions about your studies.',
            tutor: '👨‍🏫 **Tutor Mode Activated** - I\'ll provide detailed, step-by-step explanations with visual aids to help you understand concepts better. Upload documents or ask me anything!',
            notes: '📝 **Notes Mode Activated** - I\'ll create comprehensive, well-structured notes from our conversation or uploaded documents. Upload files or tell me what to focus on!',
            quiz: '❓ **Quiz Mode Activated** - I\'ll generate interactive quizzes based on our discussion or uploaded materials. Upload documents or tell me what subject to quiz you on!'
        };
        
        if (modeMessages[mode]) {
            addMessage(modeMessages[mode], 'assistant', 'mode-switch');
        }
    }
    
    console.log(`📝 Switched to ${mode} mode`);
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Check if there's an active session
    const sessionId = window.currentSessionId || window.currentSession;
    if (!sessionId || sessionId === 'default' || sessionId === 'temp') {
        showNotification('Please create a chat session first', 'warning');
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Save user message immediately - FORCE SAVE (only if session exists)
    if (sessionId && sessionId !== 'default') {
        console.log(`🔥 FORCE SAVING USER MESSAGE: ${message.substring(0, 30)}... to session: ${sessionId}`);
        saveMessageToSession(sessionId, message, 'user', 'user-input', {});
    }
    
    // Clear input
    messageInput.value = '';
    adjustTextareaHeight(messageInput);
    updateSendButton();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send via WebSocket if available, otherwise use HTTP
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                message: message,
                session_id: window.currentSession || window.currentSessionId || 'temp',
                mode: currentMode
            }));
        } else {
            // Fallback to HTTP API
            await sendMessageHTTP(message);
        }
    } catch (error) {
        console.error('Send message error:', error);
        hideTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant', 'error');
    }
}

// Send message via HTTP API
async function sendMessageHTTP(message) {
    try {
        // Get chat history for context
        const chatHistory = getChatHistory();
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: 'web_user',
                session_id: window.currentSession || window.currentSessionId || 'temp',
                mode: currentMode,
                context: {
                    has_uploads: hasUploadedDocuments(),
                    chat_history: chatHistory,
                    conversation_context: getConversationContext()
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        hideTypingIndicator();
        addMessage(data.content || data.message || 'No response received', 'assistant', data.source, data.metadata);
        
        // Text-to-speech if enabled
        if (voiceOutputEnabled && data.content) {
            speakText(data.content);
        }
        
    } catch (error) {
        hideTypingIndicator();
        console.error('HTTP API error:', error);
        addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant', 'error');
    }
}

// Get chat history for context
function getChatHistory() {
    const messages = document.querySelectorAll('.message:not(.file-upload)');
    const history = [];
    
    messages.forEach(msg => {
        const role = msg.classList.contains('user') ? 'user' : 'assistant';
        const content = msg.querySelector('.message-bubble').textContent.trim();
        
        if (content && !content.includes('Mode Activated')) {
            history.push({ role, content });
        }
    });
    
    // Return last 10 messages for context
    return history.slice(-10);
}

// Get conversation context
function getConversationContext() {
    const messages = document.querySelectorAll('.message:not(.file-upload)');
    const topics = new Set();
    const keywords = new Set();
    
    messages.forEach(msg => {
        const content = msg.querySelector('.message-bubble').textContent.toLowerCase();
        
        // Extract potential topics (simple keyword extraction)
        const words = content.split(/\s+/).filter(word => word.length > 4);
        words.forEach(word => {
            if (!['explain', 'please', 'could', 'would', 'should', 'about', 'topic'].includes(word)) {
                keywords.add(word);
            }
        });
    });
    
    return {
        message_count: messages.length,
        topics: Array.from(topics),
        keywords: Array.from(keywords).slice(0, 20), // Top 20 keywords
        current_mode: currentMode
    };
}

// Add message to chat
function addMessage(content, role, source = '', metadata = {}) {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    // Hide welcome message if it exists
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-brain"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMessageContent(content);
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    let metaContent = `<span class="timestamp">${timestamp}</span>`;
    
    if (source && source !== 'error') {
        metaContent += ` <span class="source">• ${source}</span>`;
    }
    
    if (role === 'assistant') {
        // Different actions for tutor mode vs other modes
        if (currentMode === 'tutor') {
            metaContent += `
                <div class="message-actions">
                    <button class="message-action" onclick="copyMessage(this)" title="Copy" aria-label="Copy message">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="message-action voice-control" onclick="toggleVoiceMessage(this)" title="Toggle Speech" aria-label="Toggle speech">
                        <i class="fas fa-volume-up"></i>
                    </button>
                    <button class="message-action" onclick="regenerateMessage(this)" title="Regenerate" aria-label="Regenerate message">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button class="message-action" onclick="downloadMessage(this)" title="Download as PDF" aria-label="Download message">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            `;
        } else {
            metaContent += `
                <div class="message-actions">
                    <button class="message-action" onclick="copyMessage(this)" title="Copy" aria-label="Copy message">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="message-action" onclick="regenerateMessage(this)" title="Regenerate" aria-label="Regenerate message">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button class="message-action" onclick="downloadMessage(this)" title="Download as PDF" aria-label="Download message">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            `;
        }
    }
    
    meta.innerHTML = metaContent;
    
    contentDiv.appendChild(bubble);
    contentDiv.appendChild(meta);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Save message to session immediately - FORCE SAVE (but not when loading, and only if session exists)
    const sessionId = window.currentSessionId || window.currentSession;
    if (sessionId && sessionId !== 'default' && role !== 'system' && role !== 'mode-switch' && !window.isLoadingMessages) {
        console.log(`🔥 FORCE SAVING MESSAGE: ${content.substring(0, 30)}... to session: ${sessionId}`);
        saveMessageToSession(sessionId, content, role, source, metadata);
    }
}

// Format message content (enhanced markdown support)
function formatMessageContent(content) {
    if (!content) return '';
    
    let formatted = content;
    
    // Headers
    formatted = formatted.replace(/^### (.+)$/gm, '<h3 class="msg-h3">$1</h3>');
    formatted = formatted.replace(/^## (.+)$/gm, '<h2 class="msg-h2">$1</h2>');
    formatted = formatted.replace(/^# (.+)$/gm, '<h1 class="msg-h1">$1</h1>');
    
    // Bold and italic
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks and inline code
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Lists - Numbered
    formatted = formatted.replace(/^\d+\.\s(.+)$/gm, '<li class="numbered-item">$1</li>');
    formatted = formatted.replace(/(<li class="numbered-item">.*<\/li>)/s, '<ol class="numbered-list">$1</ol>');
    
    // Lists - Bullet points
    formatted = formatted.replace(/^[-•]\s(.+)$/gm, '<li class="bullet-item">$1</li>');
    formatted = formatted.replace(/(<li class="bullet-item">.*<\/li>)/s, '<ul class="bullet-list">$1</ul>');
    
    // Tables (basic support)
    formatted = formatted.replace(/\|(.+)\|/g, (match, content) => {
        const cells = content.split('|').map(cell => `<td>${cell.trim()}</td>`).join('');
        return `<tr>${cells}</tr>`;
    });
    formatted = formatted.replace(/(<tr>.*<\/tr>)/s, '<table class="msg-table">$1</table>');
    
    // Blockquotes
    formatted = formatted.replace(/^>\s(.+)$/gm, '<blockquote class="msg-quote">$1</blockquote>');
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p class="msg-paragraph">');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!formatted.includes('<h1>') && !formatted.includes('<h2>') && !formatted.includes('<h3>') && 
        !formatted.includes('<ul>') && !formatted.includes('<ol>') && !formatted.includes('<table>')) {
        formatted = `<p class="msg-paragraph">${formatted}</p>`;
    }
    
    return formatted;
}

// Show/hide typing indicator
function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'flex';
        indicator.style.visibility = 'visible';
        
        // Scroll to bottom
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
        indicator.style.visibility = 'hidden';
    }
}

// Make hideTypingIndicator globally available
window.hideTypingIndicator = hideTypingIndicator;

// Handle keyboard input
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Adjust textarea height
function adjustTextareaHeight(textarea) {
    if (!textarea) return;
    
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// Update send button state
function updateSendButton() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    if (messageInput && sendBtn) {
        sendBtn.disabled = !messageInput.value.trim();
    }
}

// Update AI status
function updateAIStatus(status, text) {
    const aiStatus = document.getElementById('aiStatus');
    if (aiStatus) {
        aiStatus.textContent = text;
        aiStatus.className = `ai-status ${status}`;
    }
}

// Quick message functions
async function sendQuickMessage(message) {
    // Check if there's an active chat session
    if (!window.currentSessionId && !window.currentSession) {
        // No active session, create one first
        console.log('🎯 Creating session for quick message');
        await createNewSession();
        
        // Wait a moment for the interface to appear
        setTimeout(() => {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = message;
                updateSendButton();
                sendMessage();
            }
        }, 500);
    } else {
        // Session exists, send message normally
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = message;
            updateSendButton();
            sendMessage();
        }
    }
}

// Message actions
function copyMessage(button) {
    const messageContent = button.closest('.message-content').querySelector('.message-bubble').textContent;
    navigator.clipboard.writeText(messageContent).then(() => {
        // Show feedback
        const icon = button.querySelector('i');
        const originalClass = icon.className;
        icon.className = 'fas fa-check';
        setTimeout(() => {
            icon.className = originalClass;
        }, 1000);
        
        showNotification('Message copied to clipboard', 'success');
    }).catch(() => {
        showNotification('Failed to copy message', 'error');
    });
}

function speakMessage(button) {
    const messageContent = button.closest('.message-content').querySelector('.message-bubble').textContent;
    speakText(messageContent);
}

// Simple toggle voice message (single button)
function toggleVoiceMessage(button) {
    const messageContent = button.closest('.message-content').querySelector('.message-bubble').textContent;
    const icon = button.querySelector('i');
    
    if (window.speechSynthesis.speaking) {
        // Stop speaking
        window.speechSynthesis.cancel();
        icon.className = 'fas fa-volume-up';
        button.title = 'Read Message';
    } else {
        // Start speaking
        speakText(messageContent);
        icon.className = 'fas fa-stop';
        button.title = 'Stop Reading';
    }
}

function regenerateMessage(button) {
    // Get the previous user message
    const messageElement = button.closest('.message');
    const prevMessage = messageElement.previousElementSibling;
    
    if (prevMessage && prevMessage.classList.contains('user')) {
        const userMessage = prevMessage.querySelector('.message-bubble').textContent;
        
        // Remove the current assistant message
        messageElement.remove();
        
        // Resend the user message
        showTypingIndicator();
        sendMessageHTTP(userMessage);
    }
}

// Clear chat
function clearChat() {
    if (confirm('Are you sure you want to clear this chat?')) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="welcome-message" id="welcomeMessage">
                    <div class="welcome-content">
                        <div class="welcome-icon">
                            <i class="fas fa-brain"></i>
                        </div>
                        <h3>Chat Cleared!</h3>
                        <p>Start a new conversation with your AI learning companion.</p>
                    </div>
                </div>
            `;
        }
    }
}

// Check if user has uploaded documents
function hasUploadedDocuments() {
    // Check if there are any file upload messages in the chat
    const fileMessages = document.querySelectorAll('.message.file-upload');
    const hasFiles = fileMessages.length > 0;
    
    console.log(`📄 Document check: ${hasFiles ? 'Found' : 'No'} uploaded files (${fileMessages.length} files)`);
    return hasFiles;
}

// Load user preferences
function loadUserPreferences() {
    const savedTheme = localStorage.getItem('studymate-theme') || 'dark';
    const savedVoiceOutput = localStorage.getItem('studymate-voice-output') !== 'false';
    
    // Set theme (default to dark)
    document.documentElement.setAttribute('data-theme', savedTheme);
    voiceOutputEnabled = savedVoiceOutput;
    
    updateVoiceOutputIcon();
}

// Save user preferences
function saveUserPreferences() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    localStorage.setItem('studymate-theme', currentTheme);
    localStorage.setItem('studymate-voice-output', voiceOutputEnabled);
}

// Update voice output icon
function updateVoiceOutputIcon() {
    const icon = document.getElementById('voiceOutputIcon');
    if (icon) {
        icon.className = voiceOutputEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute';
    }
}

// Toggle voice output
function toggleVoiceOutput() {
    voiceOutputEnabled = !voiceOutputEnabled;
    updateVoiceOutputIcon();
    saveUserPreferences();
    
    const status = voiceOutputEnabled ? 'enabled' : 'disabled';
    showNotification(`Voice output ${status}`, 'info');
    console.log(`🔊 Voice output ${status}`);
}

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Update UI elements
function updateUI() {
    // Update session count
    updateSessionCount();
    
    // Update mode indicator
    switchMode(currentMode);
    
    // Update AI status
    updateAIStatus('ready', 'AI Ready');
}

// Update session count
function updateSessionCount() {
    const sessionCount = document.getElementById('sessionCount');
    const sessionsList = document.getElementById('sessionsList');
    
    if (sessionCount && sessionsList) {
        const sessions = sessionsList.querySelectorAll('.session-item');
        sessionCount.textContent = sessions.length;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                           type === 'error' ? 'fa-exclamation-circle' : 
                           type === 'warning' ? 'fa-exclamation-triangle' : 
                           'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()" aria-label="Close notification">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Error handling - Only log errors, don't show notifications for minor issues
window.addEventListener('error', (event) => {
    console.error('StudyMate Error:', event.error);
    
    // Only show notifications for critical errors, not minor ones
    if (event.error && event.error.message && 
        !event.error.message.includes('ResizeObserver') && 
        !event.error.message.includes('Non-Error promise rejection')) {
        updateAIStatus('error', 'System Error');
        // Don't show notification for every error - too intrusive
    }
});

// Unhandled promise rejection
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason);
    
    // Only show notifications for critical promise rejections
    if (event.reason && typeof event.reason === 'object' && event.reason.message) {
        // Don't show notification for network errors or minor issues
        if (!event.reason.message.includes('fetch') && 
            !event.reason.message.includes('NetworkError')) {
            updateAIStatus('error', 'System Error');
        }
    }
});

// Setup chat drag and drop
function setupChatDragDrop() {
    const messagesContainer = document.getElementById('messagesContainer');
    const dropOverlay = document.getElementById('chatDropOverlay');
    
    if (!messagesContainer || !dropOverlay) return;
    
    let dragCounter = 0;
    
    // Drag enter
    messagesContainer.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dragCounter++;
        if (dragCounter === 1) {
            dropOverlay.style.display = 'flex';
        }
    });
    
    // Drag over
    messagesContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    // Drag leave
    messagesContainer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            dropOverlay.style.display = 'none';
        }
    });
    
    // Drop
    messagesContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        dragCounter = 0;
        dropOverlay.style.display = 'none';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files);
        }
    });
    
    console.log('✅ Chat drag and drop setup complete');
}

// Handle file input change
function handleFileInputChange(e) {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files);
        e.target.value = ''; // Reset input
    }
}

// Track uploading files to prevent duplicates
let uploadingFiles = new Set();

// Handle file upload in chat
async function handleFileUpload(files) {
    const validFiles = Array.from(files).filter(file => {
        const validTypes = ['.pdf', '.docx', '.pptx', '.txt', '.md', '.csv', '.json'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const isValidType = validTypes.includes(fileExtension);
        const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB limit
        
        // Check if file is already being uploaded
        const fileKey = `${file.name}_${file.size}_${file.lastModified}`;
        if (uploadingFiles.has(fileKey)) {
            console.log(`File ${file.name} is already being uploaded, skipping duplicate`);
            return false;
        }
        
        if (!isValidType) {
            showNotification(`Invalid file type: ${file.name}. Supported: PDF, DOCX, PPTX, TXT, MD, CSV, JSON`, 'error');
        } else if (!isValidSize) {
            showNotification(`File too large: ${file.name}. Max size: 50MB`, 'error');
        }
        
        return isValidType && isValidSize;
    });
    
    if (validFiles.length === 0) return;
    
    // Mark files as being uploaded
    validFiles.forEach(file => {
        const fileKey = `${file.name}_${file.size}_${file.lastModified}`;
        uploadingFiles.add(fileKey);
    });
    
    // Show batch upload notification
    if (validFiles.length > 1) {
        showNotification(`Uploading ${validFiles.length} files...`, 'info');
    }
    
    // Upload files concurrently for better performance
    const uploadPromises = validFiles.map(file => uploadFileToChat(file));
    
    try {
        await Promise.all(uploadPromises);
        
        if (validFiles.length > 1) {
            showNotification(`✅ Successfully uploaded ${validFiles.length} files!`, 'success');
            
            // Add batch upload summary message
            setTimeout(() => {
                const fileNames = validFiles.map(f => f.name).join(', ');
                addMessage(
                    `📁 **Batch Upload Complete!** I've successfully processed ${validFiles.length} files: ${fileNames}. I can now answer questions about any of these documents. What would you like to explore?`,
                    'assistant',
                    'batch-upload'
                );
            }, 1000);
        }
    } catch (error) {
        console.error('Batch upload error:', error);
        showNotification(`❌ Some files failed to upload`, 'error');
    } finally {
        // Remove files from uploading set
        validFiles.forEach(file => {
            const fileKey = `${file.name}_${file.size}_${file.lastModified}`;
            uploadingFiles.delete(fileKey);
        });
    }
}

// Upload file and add to chat
async function uploadFileToChat(file) {
    // Add file upload message to chat
    addFileUploadMessage(file, 'uploading');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 'web_user');
    formData.append('session_id', window.currentSessionId || window.currentSession || 'default');
    
    try {
        console.log(`📤 Uploading ${file.name}...`);
        
        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update upload message to success with document ID
            updateFileUploadMessage(file.name, 'success', null, result.id);
            
            showNotification(`✅ Successfully uploaded ${file.name}`, 'success');
            console.log(`✅ Upload complete: ${file.name} (ID: ${result.id})`);
            
            // Refresh documents list in sidebar
            if (typeof loadDocuments === 'function') {
                loadDocuments();
            }
            
        } else {
            const errorText = await response.text();
            let errorMessage = 'Upload failed';
            
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.detail || errorMessage;
            } catch {
                errorMessage = errorText || errorMessage;
            }
            
            // Update upload message to error
            updateFileUploadMessage(file.name, 'error', errorMessage);
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Upload error:', error);
        updateFileUploadMessage(file.name, 'error', error.message);
        showNotification(`❌ Failed to upload ${file.name}: ${error.message}`, 'error');
    }
}

// Add file upload message to chat
function addFileUploadMessage(file, status, documentId = null) {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    // Hide welcome message if it exists
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message file-upload user';
    messageDiv.dataset.fileName = file.name;
    if (documentId) {
        messageDiv.dataset.documentId = documentId;
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-file-upload"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble file-bubble';
    
    const fileIcon = getFileIcon(file.name);
    const fileSize = formatFileSize(file.size);
    const fileType = file.name.split('.').pop().toUpperCase();
    
    bubble.innerHTML = `
        <div class="file-info">
            <div class="file-icon ${fileType.toLowerCase()}">
                <i class="fas ${fileIcon}"></i>
                <span class="file-type">${fileType}</span>
            </div>
            <div class="file-details">
                <div class="file-name" title="${file.name}">${file.name}</div>
                <div class="file-meta">
                    <span class="file-size">${fileSize}</span>
                    <span class="file-status-text">${status === 'uploading' ? 'Uploading...' : 
                        status === 'success' ? 'Ready to analyze' : 'Upload failed'}</span>
                </div>
            </div>
            <div class="file-actions">
                <div class="file-status">
                    ${status === 'uploading' ? '<i class="fas fa-spinner fa-spin"></i>' : 
                      status === 'success' ? '<i class="fas fa-check-circle success-icon"></i>' :
                      '<i class="fas fa-exclamation-circle error-icon"></i>'}
                </div>
                ${status === 'success' ? `
                    <div class="file-action-buttons">
                        <button class="file-action-btn" onclick="viewFileContent('${file.name}')" title="View Content" aria-label="View file content">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="file-action-btn" onclick="askAboutFile('${file.name}')" title="Ask About File" aria-label="Ask about this file">
                            <i class="fas fa-question-circle"></i>
                        </button>
                        <button class="file-action-btn delete-btn" onclick="deleteUploadedFile('${file.name}', '${documentId || ''}')" title="Delete File" aria-label="Delete file">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
        ${status === 'success' ? `
            <div class="file-preview">
                <div class="preview-placeholder">
                    <i class="fas fa-file-text"></i>
                    <span>Click <strong>View Content</strong> to preview this document</span>
                </div>
            </div>
        ` : ''}
    `;
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    meta.innerHTML = `
        <span class="timestamp">${timestamp}</span>
        ${status === 'success' ? '<span class="file-indicator">• Document uploaded</span>' : ''}
    `;
    
    contentDiv.appendChild(bubble);
    contentDiv.appendChild(meta);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Update file upload message status
function updateFileUploadMessage(fileName, status, errorMessage = '', documentId = null) {
    const fileMessage = document.querySelector(`[data-file-name="${fileName}"]`);
    if (!fileMessage) return;
    
    const statusElement = fileMessage.querySelector('.file-status');
    const statusTextElement = fileMessage.querySelector('.file-status-text');
    const actionsElement = fileMessage.querySelector('.file-actions');
    const metaElement = fileMessage.querySelector('.message-meta');
    
    if (status === 'success') {
        // Update status icon
        statusElement.innerHTML = '<i class="fas fa-check-circle success-icon"></i>';
        
        // Update status text
        if (statusTextElement) {
            statusTextElement.textContent = 'Ready to analyze';
        }
        
        // Add document ID if provided
        if (documentId) {
            fileMessage.dataset.documentId = documentId;
        }
        
        // Add action buttons
        const actionButtonsHTML = `
            <div class="file-action-buttons">
                <button class="file-action-btn" onclick="viewFileContent('${fileName}')" title="View Content" aria-label="View file content">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="file-action-btn" onclick="askAboutFile('${fileName}')" title="Ask About File" aria-label="Ask about this file">
                    <i class="fas fa-question-circle"></i>
                </button>
                <button class="file-action-btn delete-btn" onclick="deleteUploadedFile('${fileName}', '${documentId || ''}')" title="Delete File" aria-label="Delete file">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        if (actionsElement && !actionsElement.querySelector('.file-action-buttons')) {
            actionsElement.insertAdjacentHTML('beforeend', actionButtonsHTML);
        }
        
        // Add preview placeholder
        const bubble = fileMessage.querySelector('.file-bubble');
        if (bubble && !bubble.querySelector('.file-preview')) {
            bubble.insertAdjacentHTML('beforeend', `
                <div class="file-preview">
                    <div class="preview-placeholder">
                        <i class="fas fa-file-text"></i>
                        <span>Click <strong>View Content</strong> to preview this document</span>
                    </div>
                </div>
            `);
        }
        
        // Update meta
        if (metaElement) {
            const timestamp = metaElement.querySelector('.timestamp').textContent;
            metaElement.innerHTML = `
                <span class="timestamp">${timestamp}</span>
                <span class="file-indicator">• Document uploaded</span>
            `;
        }
        
    } else if (status === 'error') {
        // Update status icon
        statusElement.innerHTML = '<i class="fas fa-exclamation-circle error-icon"></i>';
        
        // Update status text
        if (statusTextElement) {
            statusTextElement.textContent = `Error: ${errorMessage}`;
        }
        
        // Add retry button
        if (actionsElement && !actionsElement.querySelector('.retry-btn')) {
            actionsElement.insertAdjacentHTML('beforeend', `
                <button class="file-action-btn retry-btn" onclick="retryFileUpload('${fileName}')" title="Retry Upload" aria-label="Retry upload">
                    <i class="fas fa-redo"></i>
                </button>
            `);
        }
    }
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
        'md': 'fa-file-alt',
        'csv': 'fa-file-csv',
        'json': 'fa-file-code',
        'xlsx': 'fa-file-excel',
        'xls': 'fa-file-excel'
    };
    return icons[extension] || 'fa-file';
}

// View file content in modal
async function viewFileContent(fileName) {
    const fileMessage = document.querySelector(`[data-file-name="${fileName}"]`);
    const documentId = fileMessage?.dataset.documentId;
    
    if (!documentId) {
        showNotification('Document ID not found', 'error');
        return;
    }
    
    try {
        showLoadingOverlay('Loading document content...');
        
        const response = await fetch(`/api/documents/${documentId}/content`);
        if (!response.ok) {
            throw new Error('Failed to load document content');
        }
        
        const data = await response.json();
        showFileContentModal(fileName, data.content, data.metadata);
        
    } catch (error) {
        console.error('Error loading file content:', error);
        showNotification(`Failed to load ${fileName}`, 'error');
    } finally {
        hideLoadingOverlay();
    }
}

// Show file content modal
function showFileContentModal(fileName, content, metadata = {}) {
    // Remove existing modal
    const existingModal = document.getElementById('fileContentModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'fileContentModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal file-content-modal">
            <div class="modal-header">
                <div class="modal-title">
                    <i class="fas ${getFileIcon(fileName)}"></i>
                    <span>${fileName}</span>
                </div>
                <div class="modal-actions">
                    <button class="modal-action-btn" onclick="downloadFileContent('${fileName}')" title="Download">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="modal-action-btn" onclick="copyFileContent()" title="Copy Content">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="modal-close" onclick="closeFileContentModal()" aria-label="Close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="modal-body">
                <div class="file-metadata">
                    <span class="metadata-item">
                        <i class="fas fa-file"></i>
                        Size: ${metadata.size || 'Unknown'}
                    </span>
                    <span class="metadata-item">
                        <i class="fas fa-calendar"></i>
                        Uploaded: ${metadata.uploaded_at ? new Date(metadata.uploaded_at).toLocaleString() : 'Unknown'}
                    </span>
                    <span class="metadata-item">
                        <i class="fas fa-align-left"></i>
                        ${metadata.pages ? `${metadata.pages} pages` : 'Text document'}
                    </span>
                </div>
                <div class="file-content-container">
                    <div class="content-toolbar">
                        <button class="toolbar-btn" onclick="toggleContentWrap()" title="Toggle Word Wrap">
                            <i class="fas fa-align-justify"></i>
                        </button>
                        <button class="toolbar-btn" onclick="increaseContentSize()" title="Increase Font Size">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="toolbar-btn" onclick="decreaseContentSize()" title="Decrease Font Size">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button class="toolbar-btn" onclick="searchInContent()" title="Search in Document">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                    <div class="file-content" id="fileContentDisplay">${formatDocumentContent(content, fileName)}</div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeFileContentModal()">Close</button>
                <button class="btn btn-primary" onclick="askAboutFile('${fileName}')">Ask About This Document</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeFileContentModal();
        }
    });
    
    // Add keyboard support
    document.addEventListener('keydown', handleFileModalKeydown);
}

// Format document content for display
function formatDocumentContent(content, fileName) {
    if (!content) return '<p class="no-content">No content available</p>';
    
    const extension = fileName.split('.').pop().toLowerCase();
    
    // Handle different file types
    if (extension === 'json') {
        try {
            const jsonObj = JSON.parse(content);
            return `<pre class="json-content">${JSON.stringify(jsonObj, null, 2)}</pre>`;
        } catch {
            return `<pre class="text-content">${escapeHtml(content)}</pre>`;
        }
    } else if (extension === 'csv') {
        return formatCSVContent(content);
    } else if (extension === 'md') {
        return formatMarkdownContent(content);
    } else {
        // Plain text or extracted content
        return `<pre class="text-content">${escapeHtml(content)}</pre>`;
    }
}

// Format CSV content as table
function formatCSVContent(csvContent) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    if (lines.length === 0) return '<p class="no-content">Empty CSV file</p>';
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const rows = lines.slice(1).map(line => line.split(',').map(cell => cell.trim().replace(/"/g, '')));
    
    let tableHTML = '<table class="csv-table"><thead><tr>';
    headers.forEach(header => {
        tableHTML += `<th>${escapeHtml(header)}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    
    rows.forEach(row => {
        tableHTML += '<tr>';
        row.forEach(cell => {
            tableHTML += `<td>${escapeHtml(cell)}</td>`;
        });
        tableHTML += '</tr>';
    });
    
    tableHTML += '</tbody></table>';
    return tableHTML;
}

// Format markdown content
function formatMarkdownContent(markdown) {
    // Basic markdown formatting
    let formatted = escapeHtml(markdown);
    
    // Headers
    formatted = formatted.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    formatted = formatted.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    formatted = formatted.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // Bold and italic
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    return `<div class="markdown-content"><p>${formatted}</p></div>`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close file content modal
function closeFileContentModal() {
    const modal = document.getElementById('fileContentModal');
    if (modal) {
        modal.remove();
    }
    document.removeEventListener('keydown', handleFileModalKeydown);
}

// Handle keyboard shortcuts in file modal
function handleFileModalKeydown(e) {
    if (e.key === 'Escape') {
        closeFileContentModal();
    }
}

// Ask about specific file
function askAboutFile(fileName) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = `Tell me about the document "${fileName}". What are the key points and main topics covered?`;
        updateSendButton();
        messageInput.focus();
        
        // Close modal if open
        closeFileContentModal();
        
        // Scroll to input
        messageInput.scrollIntoView({ behavior: 'smooth' });
    }
}

// Delete uploaded file
async function deleteUploadedFile(fileName, documentId) {
    if (!confirm(`Are you sure you want to delete "${fileName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Remove file message from chat
            const fileMessage = document.querySelector(`[data-file-name="${fileName}"]`);
            if (fileMessage) {
                fileMessage.remove();
            }
            
            // Add deletion notification to chat
            addMessage(
                `🗑️ **File Deleted:** "${fileName}" has been removed from your documents.`,
                'assistant',
                'file-deletion'
            );
            
            showNotification(`✅ Deleted ${fileName}`, 'success');
            
            // Refresh documents list
            if (typeof loadDocuments === 'function') {
                loadDocuments();
            }
            
        } else {
            throw new Error('Failed to delete document');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showNotification(`❌ Failed to delete ${fileName}`, 'error');
    }
}

// Retry file upload
async function retryFileUpload(fileName) {
    const fileMessage = document.querySelector(`[data-file-name="${fileName}"]`);
    if (!fileMessage) return;
    
    // Reset status to uploading
    updateFileUploadMessage(fileName, 'uploading');
    
    // Note: In a real implementation, you'd need to store the original file object
    // For now, we'll show a message asking user to re-upload
    showNotification('Please drag and drop the file again to retry upload', 'info');
}

// Content toolbar functions
function toggleContentWrap() {
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        content.classList.toggle('no-wrap');
    }
}

function increaseContentSize() {
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        const currentSize = parseFloat(getComputedStyle(content).fontSize);
        content.style.fontSize = (currentSize + 2) + 'px';
    }
}

function decreaseContentSize() {
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        const currentSize = parseFloat(getComputedStyle(content).fontSize);
        if (currentSize > 10) {
            content.style.fontSize = (currentSize - 2) + 'px';
        }
    }
}

function searchInContent() {
    const searchTerm = prompt('Enter text to search for:');
    if (!searchTerm) return;
    
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        // Simple text highlighting
        const text = content.textContent;
        const regex = new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi');
        const highlightedText = text.replace(regex, '<mark>$1</mark>');
        content.innerHTML = highlightedText;
    }
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Copy file content
function copyFileContent() {
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        const textContent = content.textContent;
        navigator.clipboard.writeText(textContent).then(() => {
            showNotification('Content copied to clipboard', 'success');
        }).catch(() => {
            showNotification('Failed to copy content', 'error');
        });
    }
}

// Download file content as PDF
async function downloadFileContent(fileName) {
    const content = document.getElementById('fileContentDisplay');
    if (content) {
        try {
            // Create a simple PDF using HTML to PDF conversion
            const textContent = content.textContent || content.innerText;
            
            // Create a formatted HTML document for PDF conversion
            const htmlContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>${fileName} - Content</title>
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            line-height: 1.6; 
                            margin: 40px; 
                            color: #333;
                        }
                        h1 { 
                            color: #2c3e50; 
                            border-bottom: 2px solid #3498db; 
                            padding-bottom: 10px;
                        }
                        pre { 
                            background: #f8f9fa; 
                            padding: 15px; 
                            border-radius: 5px; 
                            border-left: 4px solid #3498db;
                            white-space: pre-wrap;
                            word-wrap: break-word;
                        }
                        .header {
                            text-align: center;
                            margin-bottom: 30px;
                            padding-bottom: 20px;
                            border-bottom: 1px solid #eee;
                        }
                        .footer {
                            margin-top: 30px;
                            padding-top: 20px;
                            border-top: 1px solid #eee;
                            text-align: center;
                            font-size: 12px;
                            color: #666;
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>${fileName}</h1>
                        <p>Document Content - Generated by StudyMate AI</p>
                        <p><small>Generated on: ${new Date().toLocaleString()}</small></p>
                    </div>
                    <div class="content">
                        <pre>${textContent}</pre>
                    </div>
                    <div class="footer">
                        <p>StudyMate AI - Your Intelligent Learning Companion</p>
                    </div>
                </body>
                </html>
            `;
            
            // Create blob and download
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `${fileName}_content.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('Content downloaded as HTML (can be converted to PDF)', 'success');
            
        } catch (error) {
            console.error('Error downloading content:', error);
            showNotification('Failed to download content', 'error');
        }
    }
}

// Show/hide loading overlay
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.querySelector('span').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Get chat history for context
function getChatHistory(limit = 10) {
    const messages = document.querySelectorAll('.message:not(.file-upload)');
    const history = [];
    
    // Get last 'limit' messages
    const recentMessages = Array.from(messages).slice(-limit * 2); // *2 to account for user+assistant pairs
    
    recentMessages.forEach(messageEl => {
        const role = messageEl.classList.contains('user') ? 'user' : 'assistant';
        const content = messageEl.querySelector('.message-bubble')?.textContent?.trim();
        
        if (content && content !== 'No response received') {
            history.push({
                role: role,
                content: content,
                timestamp: new Date().toISOString()
            });
        }
    });
    
    return history;
}

// Get conversation context for better AI responses
function getConversationContext() {
    const messages = document.querySelectorAll('.message:not(.file-upload)');
    const topics = new Set();
    const keywords = new Set();
    
    messages.forEach(messageEl => {
        const content = messageEl.querySelector('.message-bubble')?.textContent?.toLowerCase();
        if (content) {
            // Extract potential topics (simple keyword extraction)
            const words = content.match(/\b\w{4,}\b/g) || [];
            words.forEach(word => {
                if (!['this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'].includes(word)) {
                    keywords.add(word);
                }
            });
        }
    });
    
    return {
        message_count: messages.length,
        topics: Array.from(topics),
        keywords: Array.from(keywords).slice(0, 20), // Limit keywords
        current_mode: currentMode,
        has_documents: hasUploadedDocuments()
    };
}

// Enhanced mode-specific message processing
function processMessageByMode(message, mode) {
    const modeInstructions = {
        tutor: 'Please provide a detailed, step-by-step explanation with examples. Break down complex concepts into simpler parts.',
        notes: 'Please create comprehensive, well-structured notes with headings, bullet points, and key concepts. Format like a textbook.',
        quiz: 'Please create quiz questions based on our previous conversation. Include multiple choice, short answer, and explanation questions.',
        chat: 'Please provide a helpful and informative response.'
    };
    
    const instruction = modeInstructions[mode] || modeInstructions.chat;
    return `${instruction}\n\nUser question: ${message}`;
}

// Load and display documents in sidebar
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents?user_id=web_user');
        if (!response.ok) {
            throw new Error('Failed to load documents');
        }
        
        const documents = await response.json();
        renderDocumentsList(documents);
        
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

// Render documents list in sidebar
function renderDocumentsList(documents) {
    const documentsList = document.getElementById('documentsList');
    const documentCount = document.getElementById('documentCount');
    
    if (!documentsList || !documentCount) return;
    
    // Update count
    documentCount.textContent = documents.length;
    
    if (documents.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-upload"></i>
                <p>No documents uploaded</p>
                <small>Drag & drop files or click + to upload</small>
            </div>
        `;
        return;
    }
    
    documentsList.innerHTML = documents.map(doc => {
        const extension = doc.filename.split('.').pop().toLowerCase();
        const fileIcon = getFileIcon(doc.filename);
        const uploadDate = new Date(doc.uploaded_at).toLocaleDateString();
        const fileSize = formatFileSize(doc.file_size || 0);
        
        return `
            <div class="document-item" data-document-id="${doc.id}" onclick="selectDocument('${doc.id}', '${doc.filename}')">
                <div class="document-icon ${extension}">
                    <i class="fas ${fileIcon}"></i>
                </div>
                <div class="document-info">
                    <div class="document-name" title="${doc.filename}">${doc.filename}</div>
                    <div class="document-meta">
                        <span>${fileSize}</span>
                        <span>•</span>
                        <span>${uploadDate}</span>
                    </div>
                </div>
                <div class="document-actions">
                    <button class="document-action" onclick="event.stopPropagation(); viewDocumentContent('${doc.id}', '${doc.filename}')" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="document-action" onclick="event.stopPropagation(); askAboutDocument('${doc.filename}')" title="Ask">
                        <i class="fas fa-question"></i>
                    </button>
                    <button class="document-action delete" onclick="event.stopPropagation(); deleteDocument('${doc.id}', '${doc.filename}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Select document in sidebar
function selectDocument(documentId, filename) {
    // Remove previous selection
    document.querySelectorAll('.document-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add selection to clicked item
    const selectedItem = document.querySelector(`[data-document-id="${documentId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Show document info or ask about it
    askAboutDocument(filename);
}

// View document content from sidebar
async function viewDocumentContent(documentId, filename) {
    try {
        showLoadingOverlay('Loading document content...');
        
        const response = await fetch(`/api/documents/${documentId}/content`);
        if (!response.ok) {
            throw new Error('Failed to load document content');
        }
        
        const data = await response.json();
        showFileContentModal(filename, data.content, data.metadata);
        
    } catch (error) {
        console.error('Error loading document content:', error);
        showNotification(`Failed to load ${filename}`, 'error');
    } finally {
        hideLoadingOverlay();
    }
}

// Ask about document from sidebar
function askAboutDocument(filename) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = `Tell me about the document "${filename}". What are the key points and main topics covered?`;
        updateSendButton();
        messageInput.focus();
        
        // Scroll to input
        messageInput.scrollIntoView({ behavior: 'smooth' });
    }
}

// Delete document from sidebar
async function deleteDocument(documentId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Reload documents list
            loadDocuments();
            
            // Remove any file messages from chat
            const fileMessages = document.querySelectorAll(`[data-file-name="${filename}"]`);
            fileMessages.forEach(msg => msg.remove());
            
            // Add deletion notification to chat
            addMessage(
                `🗑️ **File Deleted:** "${filename}" has been removed from your documents.`,
                'assistant',
                'file-deletion'
            );
            
            showNotification(`✅ Deleted ${filename}`, 'success');
            
        } else {
            throw new Error('Failed to delete document');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showNotification(`❌ Failed to delete ${filename}`, 'error');
    }
}

// Duplicate function removed - using the first one

// Save message to session - SIMPLE FILE STORAGE
async function saveMessageToSession(sessionId, content, role, source = '', metadata = {}) {
    if (!sessionId || sessionId === 'default' || sessionId === 'temp') {
        console.warn('⚠️ No valid session ID provided for message saving');
        return;
    }
    
    try {
        console.log(`💾 SAVING MESSAGE: ${content.substring(0, 30)}... to session: ${sessionId}`);
        
        // ALWAYS save to localStorage immediately
        const localMessages = JSON.parse(localStorage.getItem(`session_${sessionId}_messages`) || '[]');
        const message = {
            content: content,
            role: role,
            source: source,
            metadata: metadata,
            timestamp: new Date().toISOString(),
            id: Date.now() + Math.random()
        };
        
        localMessages.push(message);
        localStorage.setItem(`session_${sessionId}_messages`, JSON.stringify(localMessages));
        console.log(`✅ Message saved to localStorage for session ${sessionId}`);
        
        // Also try to save to server (but don't wait for it)
        fetch(`/api/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(message)
        }).then(response => {
            if (response.ok) {
                console.log(`✅ Message also saved to server for session ${sessionId}`);
            }
        }).catch(error => {
            console.log(`⚠️ Server save failed, but localStorage saved for session ${sessionId}`);
        });
        
    } catch (error) {
        console.error('❌ Error saving message:', error);
    }
}

// Download single message as PDF
function downloadMessage(button) {
    const messageContent = button.closest('.message-content').querySelector('.message-bubble');
    const messageText = messageContent.textContent || messageContent.innerText;
    const timestamp = new Date().toLocaleString();
    
    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>StudyMate AI - Message</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    margin: 40px; 
                    color: #333;
                    max-width: 800px;
                }
                .header { 
                    text-align: center; 
                    margin-bottom: 30px; 
                    padding-bottom: 20px; 
                    border-bottom: 2px solid #3b82f6;
                }
                .content { 
                    background: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px; 
                    border-left: 4px solid #3b82f6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                .footer { 
                    margin-top: 30px; 
                    text-align: center; 
                    font-size: 12px; 
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>StudyMate AI Response</h1>
                <p>Generated on: ${timestamp}</p>
            </div>
            <div class="content">${messageText}</div>
            <div class="footer">
                <p>StudyMate AI - Your Intelligent Learning Companion</p>
            </div>
        </body>
        </html>
    `;
    
    downloadAsHTML(htmlContent, `StudyMate_Message_${Date.now()}.html`);
    showNotification('Message downloaded as HTML (convertible to PDF)', 'success');
}

// Download full chat as PDF
function downloadFullChat() {
    const sessionTitle = document.getElementById('sessionTitle').textContent || 'StudyMate Chat';
    const messages = document.querySelectorAll('.message:not(.file-upload)');
    const timestamp = new Date().toLocaleString();
    
    let chatContent = '';
    messages.forEach((message, index) => {
        const role = message.classList.contains('user') ? 'You' : 'StudyMate AI';
        const content = message.querySelector('.message-bubble').textContent || '';
        const messageTime = message.querySelector('.timestamp')?.textContent || '';
        
        chatContent += `
            <div class="message-block">
                <div class="message-header">
                    <strong>${role}</strong>
                    ${messageTime ? `<span class="time">${messageTime}</span>` : ''}
                </div>
                <div class="message-content">${content}</div>
            </div>
        `;
    });
    
    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>${sessionTitle} - StudyMate AI</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    margin: 40px; 
                    color: #333;
                }
                .header { 
                    text-align: center; 
                    margin-bottom: 30px; 
                    padding-bottom: 20px; 
                    border-bottom: 2px solid #3b82f6;
                }
                .message-block { 
                    margin-bottom: 20px; 
                    padding: 15px; 
                    border-radius: 8px; 
                    background: #f8f9fa;
                    border-left: 4px solid #3b82f6;
                }
                .message-header { 
                    display: flex; 
                    justify-content: space-between; 
                    margin-bottom: 10px; 
                    font-weight: 600;
                    color: #3b82f6;
                }
                .time { 
                    font-size: 0.8rem; 
                    color: #666; 
                    font-weight: normal;
                }
                .message-content { 
                    white-space: pre-wrap; 
                    word-wrap: break-word;
                }
                .footer { 
                    margin-top: 30px; 
                    text-align: center; 
                    font-size: 12px; 
                    color: #666;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>${sessionTitle}</h1>
                <p>StudyMate AI Conversation</p>
                <p>Exported on: ${timestamp}</p>
            </div>
            <div class="chat-content">
                ${chatContent}
            </div>
            <div class="footer">
                <p>StudyMate AI - Your Intelligent Learning Companion</p>
                <p>Total Messages: ${messages.length}</p>
            </div>
        </body>
        </html>
    `;
    
    downloadAsHTML(htmlContent, `${sessionTitle.replace(/[^a-zA-Z0-9]/g, '_')}_Chat.html`);
    showNotification(`Chat "${sessionTitle}" downloaded as HTML`, 'success');
}

// Helper function to download HTML content
function downloadAsHTML(htmlContent, filename) {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Export functions for global access
window.StudyMate = {
    sendMessage,
    sendQuickMessage,
    switchMode,
    clearChat,
    toggleSidebar,
    copyMessage,
    speakMessage,
    toggleSpeakMessage,
    regenerateMessage,
    toggleVoiceOutput,
    showNotification,
    updateUI,
    handleFileUpload,
    getChatHistory,
    getConversationContext,
    loadDocuments,
    viewFileContent,
    askAboutFile,
    deleteUploadedFile,
    hideTypingIndicator,
    saveMessageToSession,
    downloadMessage,
    downloadFullChat
};

// Make functions globally available for HTML onclick
window.downloadMessage = downloadMessage;
window.downloadFullChat = downloadFullChat;
window.toggleSpeakMessage = toggleSpeakMessage;
window.toggleVoiceMessage = toggleVoiceMessage;

// Auto-initialize when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}