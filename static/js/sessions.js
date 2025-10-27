// StudyMate AI - Session Management

let sessions = [];
let currentSessionId = null;

// Load sessions from server
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions?user_id=web_user');
        if (response.ok) {
            sessions = await response.json();
            renderSessions();
            
            // Check if this is a first-time user (no sessions) or force welcome
            const urlParams = new URLSearchParams(window.location.search);
            const forceWelcome = urlParams.get('welcome') === 'true';
            
            // Always hide chat interface initially
            console.log(`🔍 Sessions loaded: ${sessions.length} sessions found`);
            hideChatInterface();
            
            // ALWAYS show welcome screen initially, never auto-enter chat
            console.log('👋 Showing welcome screen (clean interface approach)');
            showWelcomeMessage();
        } else {
            console.warn('Failed to load sessions:', response.status);
            // Show welcome screen
            showWelcomeMessage();
            hideChatInterface();
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
        // Show welcome screen on error
        showWelcomeMessage();
        hideChatInterface();
    }
}

// Create new session
async function createNewSession() {
    try {
        // Generate title based on session count
        const sessionNumber = sessions.length + 1;
        const title = `Chat ${sessionNumber}`;
        
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                mode: currentMode || 'chat',
                user_id: 'web_user'
            })
        });
        
        if (response.ok) {
            const session = await response.json();
            sessions.push(session); // Add to end instead of beginning
            
            console.log(`✅ Created new session: ${session.id} - ${session.title}`);
            switchToSession(session.id);
            renderSessions();
            
            // Clear current chat (no welcome message in chat area)
            const messagesContainer = document.getElementById('messagesContainer');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }
            
            showNotification(`Created: ${session.title}`, 'success');
        } else {
            throw new Error('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        
        // Create local session as fallback
        const sessionNumber = sessions.length + 1;
        const title = `Chat ${sessionNumber}`;
        
        const session = {
            id: 'session_' + Date.now(),
            title: title,
            mode: currentMode || 'chat',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            last_message: ''
        };
        
        console.log(`✅ Created fallback session: ${session.id} - ${session.title}`);
        sessions.push(session);
        switchToSession(session.id);
        renderSessions();
    }
}

// Hide chat interface elements
function hideChatInterface() {
    console.log('🙈 Hiding chat interface');
    
    // Use class-based approach for better control
    document.body.classList.remove('has-chat');
    document.body.classList.add('no-chat');
    
    // Hide typing indicator
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

// Show chat interface elements
function showChatInterface() {
    console.log('👁️ Showing chat interface');
    
    // Use class-based approach for better control
    document.body.classList.remove('no-chat');
    document.body.classList.add('has-chat');
    
    // Hide typing indicator when showing chat interface
    if (typeof hideTypingIndicator === 'function') {
        hideTypingIndicator();
    }
    
    // Clear messages container (remove welcome)
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
}

// Show welcome screen for users with existing sessions
function showExistingSessionsWelcome() {
    console.log('👋 Showing existing sessions welcome screen');
    
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = `
        <div class="existing-sessions-welcome">
            <div class="welcome-content">
                <div class="welcome-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <h2>Welcome back to StudyMate AI!</h2>
                <p>Select a chat from the sidebar to continue your conversation, or create a new one to start fresh.</p>
                
                <div class="welcome-actions">
                    <button class="btn btn-primary create-new-chat" onclick="showSessionNameModal()">
                        <i class="fas fa-plus"></i>
                        Create New Chat
                    </button>
                </div>
                
                <div class="existing-sessions-hint">
                    <i class="fas fa-arrow-left"></i>
                    <span>Your previous chats are available in the sidebar</span>
                </div>
            </div>
        </div>
    `;
}

// Show first-time welcome screen
function showFirstTimeWelcome() {
    console.log('👋 Showing first-time welcome screen');
    
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = `
        <div class="first-time-welcome">
            <div class="welcome-content">
                <div class="welcome-icon">
                    <i class="fas fa-graduation-cap"></i>
                </div>
                <h2>Welcome to StudyMate AI!</h2>
                <p>Your intelligent learning companion is ready to help you study, learn, and grow.</p>
                
                <div class="welcome-features">
                    <div class="feature-item">
                        <i class="fas fa-comments"></i>
                        <span>Interactive AI Chat</span>
                    </div>
                    <div class="feature-item">
                        <i class="fas fa-chalkboard-teacher"></i>
                        <span>Personal Tutoring</span>
                    </div>
                    <div class="feature-item">
                        <i class="fas fa-file-alt"></i>
                        <span>Smart Notes Generation</span>
                    </div>
                    <div class="feature-item">
                        <i class="fas fa-question-circle"></i>
                        <span>Quiz Creation</span>
                    </div>
                </div>
                
                <div class="welcome-actions">
                    <button class="btn btn-primary create-first-chat" onclick="createFirstChat()">
                        <i class="fas fa-plus"></i>
                        Create Your First Chat
                    </button>
                </div>
                
                <div class="welcome-tip">
                    <i class="fas fa-lightbulb"></i>
                    <span>Tip: You can upload documents, switch between different AI modes, and create multiple chat sessions!</span>
                </div>
            </div>
        </div>
    `;
    
    // Hide sidebar initially for clean first impression
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.add('collapsed');
    }
}

// Create first chat for new users
async function createFirstChat() {
    console.log('🎯 Creating first chat for new user');
    
    // Show loading state
    const button = document.querySelector('.create-first-chat');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        button.disabled = true;
    }
    
    try {
        // Create the first session
        await createNewSession();
        
        // Show sidebar after creating first chat
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('collapsed');
        }
        
        // Clear welcome parameter from URL
        const url = new URL(window.location);
        url.searchParams.delete('welcome');
        window.history.replaceState({}, '', url);
        
        // Show success message
        showNotification('Welcome! Your first chat is ready!', 'success');
        
    } catch (error) {
        console.error('Error creating first chat:', error);
        showNotification('Failed to create chat. Please try again.', 'error');
        
        // Reset button
        if (button) {
            button.innerHTML = '<i class="fas fa-plus"></i> Create Your First Chat';
            button.disabled = false;
        }
    }
}

// Switch to session
function switchToSession(sessionId) {
    console.log(`🔄 Switching to session: ${sessionId}`);
    
    // Stop any ongoing voice activities when switching sessions
    if (typeof stopSpeech === 'function') {
        stopSpeech();
    }
    if (typeof stopVoiceInput === 'function') {
        stopVoiceInput();
    }
    
    // Show chat interface when switching to a session
    showChatInterface();
    
    // Hide typing indicator when switching sessions
    if (typeof hideTypingIndicator === 'function') {
        hideTypingIndicator();
    }
    
    // Set ALL possible session variables
    currentSessionId = sessionId;
    currentSession = sessionId;
    window.currentSessionId = sessionId;
    window.currentSession = sessionId;
    
    console.log(`✅ Session ID set globally: ${sessionId}`);
    
    // Update UI
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.toggle('active', item.dataset.sessionId === sessionId);
    });
    
    // Load session messages
    loadSessionMessages(sessionId);
    
    // Update session info
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
        const sessionTitle = document.getElementById('sessionTitle');
        const sessionMode = document.getElementById('sessionMode');
        
        if (sessionTitle) {
            sessionTitle.textContent = session.title;
        }
        if (sessionMode) {
            sessionMode.textContent = `${session.mode.charAt(0).toUpperCase() + session.mode.slice(1)} Mode`;
        }
        
        // Update current mode to match session (without showing message)
        if (typeof switchMode === 'function') {
            switchMode(session.mode || 'chat', false);
        }
    }
    
    // Update session counter
    updateSessionCounter();
    
    console.log(`📂 Switched to session: ${sessionId}`);
}

// Load session messages - FROM LOCALSTORAGE FIRST
async function loadSessionMessages(sessionId) {
    try {
        console.log(`📂 Loading messages for session: ${sessionId}`);
        
        // Clear current messages
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '';
        
        // Hide welcome message initially
        const welcomeMessage = document.getElementById('welcomeMessage');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // FIRST: Try to load from localStorage
        const localMessages = JSON.parse(localStorage.getItem(`session_${sessionId}_messages`) || '[]');
        
        if (localMessages && localMessages.length > 0) {
            console.log(`✅ Found ${localMessages.length} messages in localStorage for session ${sessionId}`);
            
            // Sort messages by timestamp
            localMessages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Add messages to chat
            window.isLoadingMessages = true; // Flag to prevent saving during load
            
            localMessages.forEach(message => {
                if (window.addMessage && message.content && message.role) {
                    window.addMessage(message.content, message.role, message.source || '', message.metadata || {});
                }
            });
            
            window.isLoadingMessages = false; // Re-enable saving
            
            console.log(`✅ Loaded ${localMessages.length} messages from localStorage`);
        } else {
            console.log(`📭 No messages found in localStorage for session ${sessionId}`);
            
            // Try server as fallback
            try {
                const response = await fetch(`/api/sessions/${sessionId}/messages`);
                if (response.ok) {
                    const serverMessages = await response.json();
                    if (serverMessages && serverMessages.length > 0) {
                        console.log(`✅ Found ${serverMessages.length} messages on server for session ${sessionId}`);
                        serverMessages.forEach(message => {
                            if (window.addMessage) {
                                window.addMessage(message.content, message.role, message.source, message.metadata);
                            }
                        });
                    } else {
                        showWelcomeMessage();
                    }
                } else {
                    showWelcomeMessage();
                }
            } catch (serverError) {
                console.log('⚠️ Server unavailable, showing welcome message');
                showWelcomeMessage();
            }
        }
        
    } catch (error) {
        console.error('❌ Error loading session messages:', error);
        showWelcomeMessage();
    }
}

// Render sessions list
function renderSessions() {
    const sessionsList = document.getElementById('sessionsList');
    
    // Update session counter after rendering
    setTimeout(updateSessionCounter, 100);
    
    if (sessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <p>No chat sessions yet</p>
                <button class="btn btn-primary" onclick="showSessionNameModal()">
                    <i class="fas fa-plus"></i> Create Named Session
                </button>
            </div>
        `;
        return;
    }
    
    sessionsList.innerHTML = sessions.map((session, index) => `
        <div class="session-item ${session.id === currentSessionId ? 'active' : ''}" 
             data-session-id="${session.id}"
             onclick="switchToSession('${session.id}')">
            <div class="session-content">
                <div class="session-header">
                    <div class="session-number">${index + 1}</div>
                    <div class="session-info">
                        <h4 class="session-title" title="${session.title}">${session.title}</h4>
                        <div class="session-meta">
                            <span class="session-mode mode-${session.mode}">${session.mode}</span>
                            <span class="session-time">${formatSessionTime(session.updated_at || session.created_at)}</span>
                        </div>
                    </div>
                    <div class="session-actions">
                        <button class="session-action" onclick="event.stopPropagation(); showSessionNameModal('${session.id}', '${session.title}')" title="Rename Session">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="session-action" onclick="event.stopPropagation(); deleteSession('${session.id}')" title="Delete Session">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                ${session.last_message ? `<p class="session-preview" title="${session.last_message}">${session.last_message}</p>` : ''}
            </div>
        </div>
    `).join('');
}

// Update session last message
function updateSessionLastMessage(sessionId, message) {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
        session.last_message = message;
        session.updated_at = new Date().toISOString();
        renderSessions();
    }
}

// Rename session (removed duplicate - using modal version below)

// Delete session
async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this session?')) return;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            sessions = sessions.filter(s => s.id !== sessionId);
            
            // If deleting current session, switch to first available or show welcome
            if (sessionId === currentSessionId) {
                if (sessions.length > 0) {
                    switchToSession(sessions[0].id);
                } else {
                    // No sessions left, show welcome screen and hide chat interface
                    hideChatInterface();
                    showWelcomeMessage();
                    currentSessionId = null;
                    window.currentSessionId = null;
                    window.currentSession = null;
                }
            }
            
            renderSessions();
        }
    } catch (error) {
        console.error('Error deleting session:', error);
    }
}

// Format session time
function formatSessionTime(timestamp) {
    const date = new Date(timestamp);
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

// Show welcome message
function showWelcomeMessage() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-content">
                <div class="welcome-icon">
                    <i class="fas fa-graduation-cap"></i>
                </div>
                <h3>Welcome to StudyMate AI!</h3>
                <p>Your intelligent learning companion is ready to help you study, learn, and grow.</p>
                
                <div class="quick-actions">
                    <button class="quick-action" onclick="sendQuickMessage('Help me understand a concept')">
                        <i class="fas fa-lightbulb"></i>
                        Explain a Concept
                    </button>
                    <button class="quick-action" onclick="sendQuickMessage('Create study notes for me')">
                        <i class="fas fa-sticky-note"></i>
                        Generate Notes
                    </button>
                    <button class="quick-action" onclick="sendQuickMessage('Quiz me on a topic')">
                        <i class="fas fa-question-circle"></i>
                        Start a Quiz
                    </button>
                    <button class="quick-action" onclick="sendQuickMessage('Help me plan my study schedule')">
                        <i class="fas fa-calendar-alt"></i>
                        Study Planning
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Search sessions
function searchSessions(query) {
    const filteredSessions = sessions.filter(session => 
        session.title.toLowerCase().includes(query.toLowerCase()) ||
        (session.last_message && session.last_message.toLowerCase().includes(query.toLowerCase()))
    );
    
    const sessionsList = document.getElementById('sessionsList');
    
    if (filteredSessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No sessions found for "${query}"</p>
            </div>
        `;
        return;
    }
    
    // Render filtered sessions (reuse render logic)
    const originalSessions = sessions;
    sessions = filteredSessions;
    renderSessions();
    sessions = originalSessions;
}

// Archive old sessions
async function archiveOldSessions() {
    try {
        const response = await fetch('/api/sessions/archive', {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log(`Archived ${result.archived_count} old sessions`);
            loadSessions(); // Reload sessions
        }
    } catch (error) {
        console.error('Error archiving sessions:', error);
    }
}

// Export session
async function exportSession(sessionId, format = 'json') {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/export?format=${format}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `session_${sessionId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    } catch (error) {
        console.error('Error exporting session:', error);
    }
}

// Show session naming modal
function showSessionNameModal(sessionId = null, currentName = '') {
    // Remove existing modal
    const existingModal = document.getElementById('sessionNameModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const isRename = sessionId !== null;
    const modalTitle = isRename ? 'Rename Session' : 'Create New Session';
    const actionText = isRename ? 'Rename' : 'Create';
    
    const modal = document.createElement('div');
    modal.id = 'sessionNameModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal session-name-modal">
            <div class="modal-header">
                <h3>${modalTitle}</h3>
                <button class="modal-close" onclick="closeSessionNameModal()" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="input-group">
                    <label for="sessionNameInput">Session Name</label>
                    <input 
                        type="text" 
                        id="sessionNameInput" 
                        placeholder="Enter a descriptive name for your session..."
                        value="${currentName}"
                        maxlength="100"
                        autocomplete="off"
                    >
                    <small class="input-hint">Choose a name that describes what you'll be studying or working on</small>
                </div>
                
                <div class="suggested-names">
                    <label>Quick Suggestions:</label>
                    <div class="name-suggestions">
                        <button class="suggestion-btn" onclick="selectSuggestion('Study Session')">Study Session</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Homework Help')">Homework Help</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Exam Preparation')">Exam Preparation</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Research Project')">Research Project</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Math Problems')">Math Problems</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Science Notes')">Science Notes</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Essay Writing')">Essay Writing</button>
                        <button class="suggestion-btn" onclick="selectSuggestion('Quiz Practice')">Quiz Practice</button>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeSessionNameModal()">Cancel</button>
                <button class="btn btn-primary" id="sessionNameSubmit" onclick="submitSessionName('${sessionId}')" disabled>
                    <i class="fas ${isRename ? 'fa-edit' : 'fa-plus'}"></i>
                    ${actionText}
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus input and setup event listeners
    const input = document.getElementById('sessionNameInput');
    input.focus();
    input.select();
    
    // Update submit button state
    function updateSubmitButton() {
        const submitBtn = document.getElementById('sessionNameSubmit');
        const hasValue = input.value.trim().length > 0;
        const isChanged = input.value.trim() !== currentName.trim();
        submitBtn.disabled = !hasValue || (!isRename && !hasValue) || (isRename && !isChanged);
    }
    
    input.addEventListener('input', updateSubmitButton);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !document.getElementById('sessionNameSubmit').disabled) {
            submitSessionName(sessionId);
        } else if (e.key === 'Escape') {
            closeSessionNameModal();
        }
    });
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSessionNameModal();
        }
    });
    
    updateSubmitButton();
}

// Close session naming modal
function closeSessionNameModal() {
    const modal = document.getElementById('sessionNameModal');
    if (modal) {
        modal.remove();
    }
}

// Select suggestion
function selectSuggestion(name) {
    const input = document.getElementById('sessionNameInput');
    if (input) {
        input.value = name;
        input.dispatchEvent(new Event('input'));
        input.focus();
    }
}

// Submit session name
async function submitSessionName(sessionId) {
    const input = document.getElementById('sessionNameInput');
    const sessionName = input.value.trim();
    
    if (!sessionName) {
        showNotification('Please enter a session name', 'error');
        return;
    }
    
    try {
        if (sessionId) {
            // Rename existing session
            await renameSession(sessionId, sessionName);
        } else {
            // Create new session
            await createNewNamedSession(sessionName);
        }
    } catch (error) {
        console.error('Error with session name:', error);
        showNotification('Failed to save session name', 'error');
    } finally {
        // Always close the modal, regardless of success or failure
        closeSessionNameModal();
    }
}

// Create new named session
async function createNewNamedSession(title) {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                mode: currentMode || 'chat',
                user_id: 'web_user'
            })
        });
        
        if (response.ok) {
            const session = await response.json();
            sessions.push(session); // Add to end instead of beginning
            switchToSession(session.id);
            renderSessions();
            
            // Clear current chat (no welcome message in chat area)
            const messagesContainer = document.getElementById('messagesContainer');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
            }
            
            showNotification(`Created session: "${title}"`, 'success');
            updateSessionCounter();
        } else {
            throw new Error('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating named session:', error);
        showNotification('Failed to create session', 'error');
    }
}

// Rename session
async function renameSession(sessionId, newTitle) {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: newTitle
            })
        });
        
        if (response.ok) {
            session.title = newTitle;
            renderSessions();
            
            // Update header if this is current session
            if (sessionId === currentSessionId) {
                const sessionTitle = document.getElementById('sessionTitle');
                if (sessionTitle) {
                    sessionTitle.textContent = newTitle;
                }
            }
            
            showNotification(`Session renamed to "${newTitle}"`, 'success');
            updateSessionCounter();
        } else {
            throw new Error('Failed to rename session');
        }
    } catch (error) {
        console.error('Error renaming session:', error);
        showNotification('Failed to rename session', 'error');
    }
}

// Session navigation shortcuts
function navigateToNextSession() {
    if (sessions.length <= 1) return;
    
    const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
    const nextIndex = (currentIndex + 1) % sessions.length;
    switchToSession(sessions[nextIndex].id);
}

function navigateToPreviousSession() {
    if (sessions.length <= 1) return;
    
    const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
    const prevIndex = currentIndex === 0 ? sessions.length - 1 : currentIndex - 1;
    switchToSession(sessions[prevIndex].id);
}

// Update session counter in sidebar
function updateSessionCounter() {
    const sessionCounter = document.getElementById('sessionCounter');
    if (sessionCounter && sessions.length > 0) {
        const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
        if (currentIndex !== -1) {
            sessionCounter.textContent = `Session ${currentIndex + 1} of ${sessions.length}`;
        }
    }
    
    // Update navigation buttons in sidebar
    const navButtons = document.querySelectorAll('.nav-control-btn');
    const prevBtn = navButtons[0]; // Previous button
    const nextBtn = navButtons[1]; // Next button
    
    if (prevBtn && nextBtn) {
        const hasMultipleSessions = sessions.length > 1;
        prevBtn.disabled = !hasMultipleSessions;
        nextBtn.disabled = !hasMultipleSessions;
        
        // Update button text to show current position
        if (hasMultipleSessions) {
            const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
            const prevIndex = currentIndex === 0 ? sessions.length - 1 : currentIndex - 1;
            const nextIndex = (currentIndex + 1) % sessions.length;
            
            if (sessions[prevIndex]) {
                prevBtn.querySelector('span').textContent = `Previous: ${sessions[prevIndex].title}`;
            }
            if (sessions[nextIndex]) {
                nextBtn.querySelector('span').textContent = `Next: ${sessions[nextIndex].title}`;
            }
        } else {
            prevBtn.querySelector('span').textContent = 'Previous Session';
            nextBtn.querySelector('span').textContent = 'Next Session';
        }
    }
}

// Keyboard shortcuts for session navigation
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Arrow keys for session navigation
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey) {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateToPreviousSession();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateToNextSession();
        }
    }
    
    // Ctrl/Cmd + N for new session
    if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !e.shiftKey) {
        e.preventDefault();
        if (typeof showSessionNameModal === 'function') {
            showSessionNameModal();
        }
    }
});

// Edit session title directly from header
function editSessionTitle() {
    if (!currentSessionId) return;
    
    const session = sessions.find(s => s.id === currentSessionId);
    if (!session) return;
    
    showSessionNameModal(currentSessionId, session.title);
}

// Update session counter in sidebar
function updateSessionCounter() {
    const sessionCounter = document.getElementById('sessionCounter');
    if (sessionCounter && sessions.length > 0) {
        const currentIndex = sessions.findIndex(s => s.id === currentSessionId);
        if (currentIndex !== -1) {
            sessionCounter.textContent = `Session ${currentIndex + 1} of ${sessions.length}`;
        }
    }
    
    // Update navigation buttons in sidebar
    const prevBtn = document.querySelector('.nav-control-btn[onclick*="navigateToPrevious"]');
    const nextBtn = document.querySelector('.nav-control-btn[onclick*="navigateToNext"]');
    
    if (prevBtn) {
        prevBtn.disabled = sessions.length <= 1;
    }
    if (nextBtn) {
        nextBtn.disabled = sessions.length <= 1;
    }
}

// Sessions are initialized through loadSessions() called from main.js
// No automatic session creation or switching - clean interface approach

// Make session functions globally available
window.loadSessions = loadSessions;
window.createFirstChat = createFirstChat;
window.createNewSession = createNewSession;
window.switchToSession = switchToSession;

// Additional global exports for modal functions
window.showSessionNameModal = showSessionNameModal;
window.closeSessionNameModal = closeSessionNameModal;
window.submitSessionName = submitSessionName;
window.selectSuggestion = selectSuggestion;

// Interface control functions
window.hideChatInterface = hideChatInterface;
window.showChatInterface = showChatInterface;
window.showExistingSessionsWelcome = showExistingSessionsWelcome;

// Session naming functions
async function saveSessionName(sessionId) {
    const input = document.getElementById('sessionNameInput');
    const name = input.value.trim();
    
    if (!name) {
        input.focus();
        input.style.borderColor = 'var(--error)';
        setTimeout(() => {
            input.style.borderColor = '';
        }, 2000);
        return;
    }
    
    try {
        if (sessionId) {
            // Rename existing session
            await renameSession(sessionId, name);
        } else {
            // Create new session with custom name
            await createNewSessionWithName(name);
        }
        
        // Close modal
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
        
    } catch (error) {
        console.error('Error saving session name:', error);
        showNotification('Failed to save session name', 'error');
    }
}

async function createNewSessionWithName(name) {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: name,
                mode: currentMode || 'chat',
                user_id: 'web_user'
            })
        });
        
        if (response.ok) {
            const session = await response.json();
            
            // Add to sessions list
            if (typeof sessions !== 'undefined') {
                sessions.unshift(session);
            }
            
            // Switch to new session
            if (typeof switchToSession === 'function') {
                switchToSession(session.id);
            }
            
            // Re-render sessions
            if (typeof renderSessions === 'function') {
                renderSessions();
            }
            
            showNotification(`Created session "${name}"`, 'success');
        } else {
            throw new Error('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        showNotification('Failed to create session', 'error');
    }
}

// Make functions globally available
window.saveSessionName = saveSessionName;
window.createNewSessionWithName = createNewSessionWithName;