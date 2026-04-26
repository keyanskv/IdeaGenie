document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const modeSelect = document.getElementById('mode-select');
    const modelSelect = document.getElementById('model-select');
    const apiTokenInput = document.getElementById('api-token');
    const saveTokenBtn = document.getElementById('save-token');
    const providerSelect = document.getElementById('provider-select');
    const clearChatBtn = document.getElementById('clear-chat');
    const totalCostSpan = document.getElementById('total-cost');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const attachmentPreview = document.getElementById('attachment-preview');
    const fileNameSpan = attachmentPreview.querySelector('.file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const webSearchToggle = document.getElementById('web-search-toggle');

    function renderMarkdown(text) {
        if (!text) return "";
        
        // 1. Preserve newlines by splitting into paragraphs first
        let blocks = text.split(/\n\n+/);
        
        return blocks.map(block => {
            // 2. Headings
            block = block.replace(/^### (.*$)/gm, '<h3>$1</h3>');
            block = block.replace(/^## (.*$)/gm, '<h2>$1</h2>');
            block = block.replace(/^# (.*$)/gm, '<h1>$1</h1>');
            
            // 3. Bold
            block = block.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            // 4. Code Blocks
            block = block.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
            
            // 5. Inline Code
            block = block.replace(/`([^`]+)`/g, '<code>$1</code>');
            
            // 6. Lists
            block = block.replace(/^\- (.*$)/gm, '<li>$1</li>');
            if (block.includes('<li>')) {
                block = '<ul>' + block + '</ul>';
            }
            
            // 7. Standard paragraphs (if not already a tag)
            if (!block.startsWith('<h') && !block.startsWith('<pre') && !block.startsWith('<ul')) {
                return `<p>${block.replace(/\n/g, '<br>')}</p>`;
            }
            return block;
        }).join('');
    }

    let currentAttachment = null;

    async function updateStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            totalCostSpan.textContent = `$${data.total_cost.toFixed(4)}`;
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    }

    function appendMessage(role, content) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${role}`;

        const msg = document.createElement('div');
        msg.className = `message ${role}`;
        
        if (role === 'ai') {
            msg.innerHTML = renderMarkdown(content);
        } else {
            msg.textContent = content;
        }

        wrapper.appendChild(msg);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleSend() {
        const message = userInput.value.trim();
        if (!message) return;

        const mode = modeSelect.value;
        const modelId = modelSelect.value;
        const attachmentContent = currentAttachment ? currentAttachment.content : null;

        userInput.value = '';
        if (currentAttachment) clearAttachment();
        appendMessage('user', message);

        // Add loading state message
        const loadingId = 'ai-loading-' + Date.now();
        const loadingWrapper = document.createElement('div');
        loadingWrapper.className = 'message-wrapper ai';
        loadingWrapper.id = loadingId;
        loadingWrapper.innerHTML = `<div class="message ai"><span class="thinking-dot"></span><span class="thinking-dot" style="animation-delay: 0.2s"></span><span class="thinking-dot" style="animation-delay: 0.4s"></span></div>`;
        chatMessages.appendChild(loadingWrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        let aiMessageContent = "";
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message ai';
        aiMessageDiv.style.display = 'none';

        const aiWrapper = document.createElement('div');
        aiWrapper.className = 'message-wrapper ai';
        aiWrapper.appendChild(aiMessageDiv);

        try {
            // Use streaming for most modes, except for agentic which is too complex for simple SSE
            if (mode === 'agentic' || mode === 'ensemble' || mode === 'pipeline') {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message, mode, model_id: modelId, attachment: attachmentContent
                    })
                });
                const data = await response.json();
                document.getElementById(loadingId).remove();
                if (data.error) appendMessage('ai', 'Error: ' + data.error);
                else appendMessage('ai', data.content);
                updateStats();
                return;
            }

            // Streaming Logic (SSE)
            const params = new URLSearchParams({
                message, mode, model_id: modelId, attachment: attachmentContent || ""
            });
            const eventSource = new EventSource(`/chat_stream?${params.toString()}`);

            eventSource.onmessage = (event) => {
                if (document.getElementById(loadingId)) {
                    document.getElementById(loadingId).remove();
                    chatMessages.appendChild(aiWrapper);
                    aiMessageDiv.style.display = 'block';
                }

                if (event.data === '[DONE]') {
                    eventSource.close();
                    updateStats();
                    return;
                }

                aiMessageContent += event.data;
                aiMessageDiv.innerHTML = renderMarkdown(aiMessageContent);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            };

            eventSource.onerror = (err) => {
                console.error("EventSource failed:", err);
                eventSource.close();
                if (document.getElementById(loadingId)) document.getElementById(loadingId).remove();
                appendMessage('ai', 'Streaming connection failed.');
            };

        } catch (err) {
            if (document.getElementById(loadingId)) document.getElementById(loadingId).remove();
            appendMessage('ai', 'Connection error. Is the server running?');
        }
    }

    saveTokenBtn.addEventListener('click', async () => {
        const token = apiTokenInput.value.trim();
        const provider = providerSelect.value;
        if (!token) return;

        const response = await fetch('/set_token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, token })
        });

        const data = await response.json();
        if (data.status === 'success') {
            apiTokenInput.value = '';
            alert(`${provider} token updated successfully!`);
        }
    });

    clearChatBtn.addEventListener('click', async () => {
        await fetch('/clear', { method: 'POST' });
        chatMessages.innerHTML = '';
        appendMessage('ai', 'Memory cleared. How can I help you?');
    });

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    uploadBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            fileNameSpan.textContent = `Uploading ${file.name}...`;
            attachmentPreview.style.display = 'flex';

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.status === 'success') {
                currentAttachment = {
                    name: file.name,
                    content: data.content
                };
                fileNameSpan.textContent = file.name;
            } else {
                alert('Upload failed: ' + data.error);
                clearAttachment();
            }
        } catch (err) {
            alert('Upload error. See console.');
            console.error(err);
            clearAttachment();
        }
    });

    function clearAttachment() {
        currentAttachment = null;
        fileInput.value = '';
        attachmentPreview.style.display = 'none';
    }

    removeFileBtn.addEventListener('click', clearAttachment);
});
