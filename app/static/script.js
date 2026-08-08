document.addEventListener('DOMContentLoaded', () => {
    // State
    let sessionId = generateSessionId();
    
    // DOM Elements
    const sessionIdDisplay = document.getElementById('sessionIdDisplay');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const clearMemoryBtn = document.getElementById('clearMemoryBtn');
    
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // Initialize
    sessionIdDisplay.textContent = sessionId.substring(0, 8);
    
    // --- Utility Functions ---
    function generateSessionId() {
        return 'sess_' + Math.random().toString(36).substring(2, 15);
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function setStatus(element, message, type) {
        element.textContent = message;
        element.className = `status-message status-${type}`;
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }
    
    // --- File Upload Logic ---
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    async function handleFileUpload(file) {
        if (file.type !== 'application/pdf') {
            setStatus(uploadStatus, 'Please upload a valid PDF file.', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        setStatus(uploadStatus, 'Uploading and ingesting...', 'success');
        
        try {
            const response = await fetch('/api/v1/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (response.ok) {
                setStatus(uploadStatus, result.message, 'success');
            } else {
                setStatus(uploadStatus, result.detail || 'Upload failed.', 'error');
            }
        } catch (error) {
            console.error('Upload Error:', error);
            setStatus(uploadStatus, 'An error occurred during upload.', 'error');
        }
    }
    
    // --- Chat Logic ---
    function addMessageToUI(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'system-message'}`;
        
        const avatarSvg = isUser 
            ? '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
            : '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
            
        messageDiv.innerHTML = `
            <div class="avatar">${avatarSvg}</div>
            <div class="message-content"></div>
        `;
        
        // We will just use textContent for safety, though for markdown we'd use a parser.
        // For simplicity, we just set innerText.
        messageDiv.querySelector('.message-content').innerText = content;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv.querySelector('.message-content');
    }
    
    function addTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message typing-container';
        messageDiv.id = 'typingIndicator';
        
        messageDiv.innerHTML = `
            <div class="avatar">
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <div class="message-content" style="padding: 12px 20px;">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }
    
    // Auto-resize textarea
    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Submit on Enter (prevent default if not shift)
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Disable input
        questionInput.value = '';
        questionInput.style.height = 'auto';
        questionInput.disabled = true;
        sendBtn.disabled = true;
        
        // Add user message
        addMessageToUI(question, true);
        
        addTypingIndicator();
        
        try {
            const response = await fetch('/api/v1/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    question: question
                })
            });
            
            removeTypingIndicator();
            
            if (!response.ok) {
                const errResult = await response.json();
                addMessageToUI(`Error: ${errResult.detail || 'Failed to get response.'}`, false);
                return;
            }
            
            // Streaming Logic
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            // Create a placeholder message for the stream
            const responseContentDiv = addMessageToUI('', false);
            let aiResponse = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                aiResponse += chunk;
                responseContentDiv.innerText = aiResponse;
                scrollToBottom();
            }
            
        } catch (error) {
            console.error('Chat Error:', error);
            removeTypingIndicator();
            addMessageToUI('Sorry, there was an error connecting to the server.', false);
        } finally {
            // Re-enable input
            questionInput.disabled = false;
            sendBtn.disabled = false;
            questionInput.focus();
        }
    });
    
    // --- Memory Management ---
    clearMemoryBtn.addEventListener('click', async () => {
        if(!confirm('Are you sure you want to clear this session memory?')) return;
        
        try {
            const response = await fetch(`/api/v1/memory/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                chatMessages.innerHTML = '';
                addMessageToUI('Session memory cleared. How can I help you next?', false);
            }
        } catch (error) {
            console.error('Error clearing memory:', error);
            alert('Failed to clear memory');
        }
    });
});
