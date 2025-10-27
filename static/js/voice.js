// StudyMate AI - Enhanced Voice Interface

let recognition = null;
let synthesis = null;
let isListening = false;
let currentUtterance = null;
let voiceEnabled = false;

// Initialize voice features
function initializeVoice() {
    console.log('🎤 Initializing voice features...');
    
    // Check if showNotification is available
    if (typeof showNotification !== 'function') {
        console.warn('showNotification function not available');
        window.showNotification = function(msg, type) {
            console.log(`${type.toUpperCase()}: ${msg}`);
        };
    }
    
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            isListening = true;
            updateVoiceButton();
            showNotification('Listening... Speak now!', 'info');
        };
        
        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                if (finalTranscript) {
                    messageInput.value = finalTranscript;
                    updateSendButton();
                    
                    // Auto-send if enabled
                    const autoSend = localStorage.getItem('studymate-voice-auto-send') === 'true';
                    if (autoSend) {
                        setTimeout(() => {
                            sendMessage();
                        }, 500);
                    }
                } else if (interimTranscript) {
                    // Show interim results in placeholder
                    messageInput.placeholder = `Listening: ${interimTranscript}`;
                }
            }
        };
        
        recognition.onend = () => {
            console.log('🎤 Voice recognition ended');
            isListening = false;
            updateVoiceButton();
            
            // Reset placeholder
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                const placeholder = {
                    chat: 'Ask me anything about your studies...',
                    tutor: 'What would you like me to explain step by step?',
                    notes: 'What topic should I create comprehensive notes for?',
                    quiz: 'What subject would you like to be quizzed on?'
                };
                messageInput.placeholder = placeholder[currentMode] || placeholder.chat;
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            isListening = false;
            updateVoiceButton();
            
            let errorMessage = 'Voice recognition error';
            switch (event.error) {
                case 'not-allowed':
                    errorMessage = 'Microphone access denied. Please enable microphone permissions.';
                    break;
                case 'no-speech':
                    errorMessage = 'No speech detected. Please try again.';
                    break;
                case 'audio-capture':
                    errorMessage = 'No microphone found. Please check your audio settings.';
                    break;
                case 'network':
                    errorMessage = 'Network error during voice recognition.';
                    break;
                default:
                    errorMessage = `Voice recognition error: ${event.error}`;
            }
            
            showNotification(errorMessage, 'error');
        };
        
        voiceEnabled = true;
        console.log('✅ Voice recognition initialized');
    } else {
        console.log('❌ Voice recognition not supported');
        voiceEnabled = false;
    }
    
    // Initialize speech synthesis
    if ('speechSynthesis' in window) {
        synthesis = window.speechSynthesis;
        
        // Load voices
        loadVoices();
        
        // Listen for voices changed event
        if (synthesis.onvoiceschanged !== undefined) {
            synthesis.onvoiceschanged = loadVoices;
        }
        
        console.log('✅ Speech synthesis initialized');
    } else {
        console.log('❌ Speech synthesis not supported');
    }
    
    updateVoiceButton();
}

// Load available voices
function loadVoices() {
    if (!synthesis) return;
    
    const voices = synthesis.getVoices();
    console.log(`🔊 Loaded ${voices.length} voices`);
    
    // Find preferred voice (English, natural sounding)
    const preferredVoice = voices.find(voice => 
        voice.lang.startsWith('en') && 
        (voice.name.includes('Natural') || voice.name.includes('Enhanced') || voice.name.includes('Premium'))
    ) || voices.find(voice => voice.lang.startsWith('en'));
    
    if (preferredVoice) {
        console.log(`🎯 Selected voice: ${preferredVoice.name}`);
    }
}

// Toggle voice input
function toggleVoiceInput() {
    console.log('🎤 Toggle voice input called, voiceEnabled:', voiceEnabled);
    
    if (!voiceEnabled) {
        if (typeof showNotification === 'function') {
            showNotification('Voice input is not supported in your browser', 'error');
        } else {
            alert('Voice input is not supported in your browser');
        }
        return;
    }
    
    if (isListening) {
        stopVoiceInput();
    } else {
        startVoiceInput();
    }
}

// Start voice input
function startVoiceInput() {
    if (!recognition || !voiceEnabled) {
        showNotification('Voice recognition not available', 'error');
        return;
    }
    
    try {
        // Stop any ongoing speech
        if (synthesis && synthesis.speaking) {
            synthesis.cancel();
        }
        
        // Clear current input
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = '';
            updateSendButton();
        }
        
        recognition.start();
        
        console.log('🎤 Starting voice input...');
        
    } catch (error) {
        console.error('Error starting voice input:', error);
        showNotification('Failed to start voice input', 'error');
        isListening = false;
        updateVoiceButton();
    }
}

// Stop voice input
function stopVoiceInput() {
    if (!recognition) return;
    
    try {
        recognition.stop();
        console.log('🎤 Stopping voice input...');
        
    } catch (error) {
        console.error('Error stopping voice input:', error);
    }
}

// Speak text using browser TTS (only in tutor mode)
function speakText(text) {
    // Only speak in tutor mode
    if (typeof currentMode !== 'undefined' && currentMode !== 'tutor') {
        console.log('Voice output disabled - not in tutor mode');
        return;
    }
    
    if (!synthesis) {
        console.log('Speech synthesis not available');
        if (typeof showNotification === 'function') {
            showNotification('Speech synthesis not available in your browser', 'warning');
        }
        return;
    }
    
    // Stop any ongoing speech
    if (synthesis.speaking) {
        synthesis.cancel();
    }
    
    // Clean text for speech - Remove ALL markdown and formatting
    const cleanText = text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown **text**
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown *text*
        .replace(/`(.*?)`/g, '$1') // Remove code markdown `text`
        .replace(/#{1,6}\s/g, '') // Remove markdown headers # ## ###
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links [text](url) -> text
        .replace(/<[^>]*>/g, '') // Remove HTML tags
        .replace(/\*+/g, '') // Remove any remaining asterisks
        .replace(/#/g, '') // Remove hash symbols
        .replace(/`/g, '') // Remove backticks
        .replace(/\n/g, ' ') // Replace newlines with spaces
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();
    
    if (!cleanText || cleanText.length === 0) {
        console.log('No text to speak');
        return;
    }
    
    // Don't limit text length - speak the full response
    const textToSpeak = cleanText;
    
    // Split long text into chunks for better handling
    const chunks = splitTextIntoChunks(textToSpeak, 200);
    speakTextChunks(chunks, 0);
}

// Split text into manageable chunks
function splitTextIntoChunks(text, maxLength) {
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const chunks = [];
    let currentChunk = '';
    
    for (const sentence of sentences) {
        const trimmedSentence = sentence.trim();
        if (currentChunk.length + trimmedSentence.length + 1 <= maxLength) {
            currentChunk += (currentChunk ? '. ' : '') + trimmedSentence;
        } else {
            if (currentChunk) {
                chunks.push(currentChunk + '.');
            }
            currentChunk = trimmedSentence;
        }
    }
    
    if (currentChunk) {
        chunks.push(currentChunk + '.');
    }
    
    return chunks;
}

// Speak text chunks sequentially
function speakTextChunks(chunks, index) {
    if (index >= chunks.length) {
        console.log('🔊 Finished speaking all chunks');
        updateSpeechButtons(false);
        return;
    }
    
    const chunk = chunks[index];
    currentUtterance = new SpeechSynthesisUtterance(chunk);
    
    // Configure voice settings for female voice
    currentUtterance.rate = parseFloat(localStorage.getItem('studymate-voice-rate') || '0.8');
    currentUtterance.pitch = parseFloat(localStorage.getItem('studymate-voice-pitch') || '1.2');
    currentUtterance.volume = parseFloat(localStorage.getItem('studymate-voice-volume') || '0.9');
    
    // Try to use a female voice
    const voices = synthesis.getVoices();
    const femaleVoice = voices.find(voice => 
        voice.lang.startsWith('en') && 
        (voice.name.toLowerCase().includes('female') || 
         voice.name.toLowerCase().includes('woman') ||
         voice.name.toLowerCase().includes('samantha') ||
         voice.name.toLowerCase().includes('victoria') ||
         voice.name.toLowerCase().includes('karen'))
    ) || voices.find(voice => voice.lang.startsWith('en'));
    
    if (femaleVoice) {
        currentUtterance.voice = femaleVoice;
        console.log(`🔊 Using voice: ${femaleVoice.name}`);
    }
    
    currentUtterance.onstart = () => {
        console.log(`🔊 Started speaking chunk ${index + 1}/${chunks.length}`);
        if (index === 0) {
            updateSpeechButtons(true);
        }
    };
    
    currentUtterance.onend = () => {
        console.log(`🔊 Finished chunk ${index + 1}/${chunks.length}`);
        
        if (index + 1 >= chunks.length) {
            // All chunks finished, reset voice buttons
            resetAllVoiceButtons();
        } else {
            // Continue with next chunk after a short pause
            setTimeout(() => {
                speakTextChunks(chunks, index + 1);
            }, 300);
        }
    };
    
    currentUtterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
        
        // Handle different error types
        if (event.error === 'interrupted') {
            console.log('Speech was interrupted (normal when stopping)');
            return;
        }
        
        // Reset buttons and state
        updateSpeechButtons(false);
        currentUtterance = null;
        
        // Reset all voice control buttons
        resetAllVoiceButtons();
        
        // Only show error for actual errors, not interruptions
        if (event.error !== 'canceled' && event.error !== 'interrupted') {
            showNotification('Speech synthesis error: ' + event.error, 'error');
        }
    };
    
    try {
        synthesis.speak(currentUtterance);
        console.log(`🔊 Speaking chunk ${index + 1}: "${chunk.substring(0, 50)}..."`);
    } catch (error) {
        console.error('Error speaking text:', error);
        showNotification('Failed to speak text', 'error');
    }
}

// Stop speech
function stopSpeech() {
    if (synthesis && synthesis.speaking) {
        synthesis.cancel();
        console.log('🔊 Speech stopped');
    }
    
    if (currentUtterance) {
        currentUtterance = null;
    }
    
    updateSpeechButtons(false);
}

// Update voice button state
function updateVoiceButton() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (!voiceBtn) {
        console.warn('Voice button not found in DOM');
        return;
    }
    
    if (!voiceEnabled) {
        voiceBtn.style.display = 'none';
        return;
    }
    
    voiceBtn.style.display = 'flex';
    
    const icon = voiceBtn.querySelector('i');
    if (icon) {
        if (isListening) {
            icon.className = 'fas fa-stop';
            voiceBtn.classList.add('listening');
            voiceBtn.title = 'Stop listening';
        } else {
            icon.className = 'fas fa-microphone';
            voiceBtn.classList.remove('listening');
            voiceBtn.title = 'Start voice input (Ctrl+Shift+V)';
        }
    }
}

// Update speech button states
function updateSpeechButtons(isSpeaking) {
    const speechButtons = document.querySelectorAll('.message-action[title*="Speak"]');
    speechButtons.forEach(btn => {
        const icon = btn.querySelector('i');
        if (icon) {
            if (isSpeaking) {
                icon.className = 'fas fa-stop';
                btn.title = 'Stop speaking';
            } else {
                icon.className = 'fas fa-volume-up';
                btn.title = 'Speak message';
            }
        }
    });
}

// Voice command processing
function processVoiceCommand(text) {
    const command = text.toLowerCase().trim();
    
    // Mode switching commands
    if (command.includes('switch to chat mode') || command === 'chat mode') {
        switchMode('chat');
        showNotification('Switched to Chat mode', 'success');
        return true;
    }
    
    if (command.includes('switch to tutor mode') || command === 'tutor mode') {
        switchMode('tutor');
        showNotification('Switched to Tutor mode', 'success');
        return true;
    }
    
    if (command.includes('switch to notes mode') || command === 'notes mode') {
        switchMode('notes');
        showNotification('Switched to Notes mode', 'success');
        return true;
    }
    
    if (command.includes('switch to quiz mode') || command === 'quiz mode') {
        switchMode('quiz');
        showNotification('Switched to Quiz mode', 'success');
        return true;
    }
    
    // Navigation commands
    if (command.includes('new session') || command.includes('new chat')) {
        createNewSession();
        showNotification('Created new session', 'success');
        return true;
    }
    
    if (command.includes('clear chat') || command.includes('clear conversation')) {
        clearChat();
        showNotification('Chat cleared', 'success');
        return true;
    }
    
    // Settings commands
    if (command.includes('toggle voice output') || command.includes('mute voice')) {
        toggleVoiceOutput();
        return true;
    }
    
    if (command.includes('stop speaking') || command === 'stop') {
        stopSpeech();
        showNotification('Speech stopped', 'info');
        return true;
    }
    
    return false; // Not a recognized command
}

// Voice shortcuts
const voiceShortcuts = {
    'help': 'What can I help you with today?',
    'explain': 'What would you like me to explain?',
    'notes': 'What topic should I create notes for?',
    'quiz': 'What subject would you like to be quizzed on?',
    'study plan': 'Help me create a study plan',
    'summarize': 'Please summarize this content for me',
    'homework': 'Help me with my homework',
    'research': 'Help me research a topic'
};

// Handle voice shortcuts
function handleVoiceShortcut(text) {
    const shortcut = text.toLowerCase().trim();
    
    if (voiceShortcuts[shortcut]) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = voiceShortcuts[shortcut];
            updateSendButton();
            showNotification(`Voice shortcut: ${shortcut}`, 'info');
        }
        return true;
    }
    
    return false;
}

// Voice settings management
const voiceSettings = {
    autoSend: false,
    continuousListening: false,
    voiceCommands: true,
    rate: 0.9,
    pitch: 1.0,
    volume: 0.8
};

// Load voice settings
function loadVoiceSettings() {
    const saved = localStorage.getItem('studymate-voice-settings');
    if (saved) {
        try {
            Object.assign(voiceSettings, JSON.parse(saved));
        } catch (error) {
            console.error('Error loading voice settings:', error);
        }
    }
}

// Save voice settings
function saveVoiceSettings() {
    localStorage.setItem('studymate-voice-settings', JSON.stringify(voiceSettings));
}

// Update voice settings
function updateVoiceSetting(key, value) {
    voiceSettings[key] = value;
    saveVoiceSettings();
    
    // Apply settings immediately
    switch (key) {
        case 'rate':
            localStorage.setItem('studymate-voice-rate', value);
            break;
        case 'pitch':
            localStorage.setItem('studymate-voice-pitch', value);
            break;
        case 'volume':
            localStorage.setItem('studymate-voice-volume', value);
            break;
        case 'autoSend':
            localStorage.setItem('studymate-voice-auto-send', value);
            break;
    }
}

// Voice accessibility features
function enableVoiceAccessibility() {
    // Keyboard shortcuts for voice
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Shift + V for voice input
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
            e.preventDefault();
            toggleVoiceInput();
        }
        
        // Ctrl/Cmd + Shift + S to stop speech
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            stopSpeech();
        }
        
        // Escape to stop voice input or speech
        if (e.key === 'Escape') {
            if (isListening) {
                stopVoiceInput();
            }
            if (synthesis && synthesis.speaking) {
                stopSpeech();
            }
        }
    });
}

// Check browser compatibility
function checkVoiceCompatibility() {
    const compatibility = {
        speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
        speechSynthesis: 'speechSynthesis' in window,
        mediaDevices: 'mediaDevices' in navigator
    };
    
    console.log('🎤 Voice compatibility:', compatibility);
    return compatibility;
}

// Initialize voice features on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check compatibility first
    const compatibility = checkVoiceCompatibility();
    
    console.log('🎤 Voice compatibility check:', compatibility);
    
    if (compatibility.speechRecognition || compatibility.speechSynthesis) {
        loadVoiceSettings();
        enableVoiceAccessibility();
        
        // Initialize after a short delay to ensure other components are ready
        setTimeout(() => {
            initializeVoice();
            
            // Ensure voice button is visible if voice is supported
            setTimeout(() => {
                const voiceBtn = document.getElementById('voiceBtn');
                if (voiceBtn && voiceEnabled) {
                    voiceBtn.style.display = 'flex';
                    console.log('✅ Voice button made visible');
                }
            }, 100);
        }, 500);
    } else {
        console.log('❌ Voice features not supported in this browser');
        // Hide voice button if not supported
        setTimeout(() => {
            const voiceBtn = document.getElementById('voiceBtn');
            if (voiceBtn) {
                voiceBtn.style.display = 'none';
            }
        }, 100);
    }
});

// Export voice functions for global access
window.VoiceInterface = {
    toggleVoiceInput,
    startVoiceInput,
    stopVoiceInput,
    speakText,
    stopSpeech,
    processVoiceCommand,
    handleVoiceShortcut,
    updateVoiceSetting,
    checkVoiceCompatibility
};

// Reset all voice buttons to default state
function resetAllVoiceButtons() {
    document.querySelectorAll('.voice-control').forEach(button => {
        const icon = button.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-volume-up';
            button.title = 'Read Message';
        }
    });
}

// Make function globally available
window.resetAllVoiceButtons = resetAllVoiceButtons;