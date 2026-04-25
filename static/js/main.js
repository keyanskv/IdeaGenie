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

    function appendMessage(role, content) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${role}`;
        
        const msg = document.createElement('div');
        msg.className = `message ${role}`;
        msg.textContent = content;
        
        wrapper.appendChild(msg);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleSend() {
        const message = userInput.value.trim();
        if (!message) return;

        userInput.value = '';
        appendMessage('user', message);

        // Add loading state
        const loadingId = 'ai-loading-' + Date.now();
        const loadingWrapper = document.createElement('div');
        loadingWrapper.className = 'message-wrapper ai';
        loadingWrapper.id = loadingId;
        loadingWrapper.innerHTML = `<div class="message ai">Thinking...</div>`;
        chatMessages.appendChild(loadingWrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    mode: modeSelect.value,
                    model_id: modelSelect.value
                })
            });
            
            const data = await response.json();
            document.getElementById(loadingId).remove();

            if (data.error) {
                appendMessage('ai', 'Error: ' + data.error);
            } else {
                appendMessage('ai', data.content);
            }
        } catch (err) {
            document.getElementById(loadingId).remove();
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
});
