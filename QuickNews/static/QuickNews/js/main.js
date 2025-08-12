document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Elements ---
    const sidebar = document.getElementById('sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const welcomeScreen = document.getElementById('welcome-screen');
    const historyContainer = document.getElementById('history-container');
    const chatTitle = document.getElementById('chat-title');
    const searchToggleBtn = document.getElementById('search-toggle-btn');

    // --- State for animation timer ---
    let spinnerAnimationTimer = null;

    // --- Helper Functions ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function isURL(str) {
        // A more robust regex to validate URLs, including those without http/https
        const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
            '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
            '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
            '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
            '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
            '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
        return !!pattern.test(str);
    }

    // --- UI Interaction ---
    function setInitialSidebarState() {
        if (window.innerWidth < 640) {
            sidebar.classList.remove('is-open');
        } else {
            sidebar.classList.remove('is-collapsed');
        }
    }

    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle(window.innerWidth < 640 ? 'is-open' : 'is-collapsed');
    });

    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${Math.min(messageInput.scrollHeight, 200)}px`;
        updateSendButtonState();
    });

    function updateSendButtonState() {
        const isActive = messageInput.value.trim().length > 0;
        sendBtn.classList.toggle('send-active', isActive);
        sendBtn.disabled = !isActive;
    }
    
    // --- Messaging Core ---
    async function sendMessage() {
        const messageText = messageInput.value.trim();
        if (messageText === '') return;

        welcomeScreen?.classList.add('hidden');
        addMessage(messageText, 'user');
        messageInput.value = '';
        messageInput.style.height = 'auto';
        updateSendButtonState();
        showTypingIndicator();

        try {
            const isSearchActive = searchToggleBtn.classList.contains('search-active');
            const isUrlInput = isURL(messageText);

            let endpoint;
            let payload;

            if (isSearchActive) {
                endpoint = '/search_with_context/';
                payload = { query: messageText };
            } else if (isUrlInput) {
                endpoint = '/process-article/';
                payload = { url: messageText };
            } else {
                endpoint = '/process-article/';
                payload = { query: messageText };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            hideTypingIndicator();

            if (result.success) {
                if (result.type === 'article') {
                    const formatted = formatArticleResponse(result.data);
                    addMessage(formatted, 'assistant', true);
                    if (!result.from_cache) {
                         await loadHistory();
                    }
                    chatTitle.textContent = result.data.short_title;
                    setActiveHistoryItem(result.data.id);
                } else if (result.type === 'search') {
                    addMessage(result.data.answer, 'assistant', true);
                }
            } else {
                addMessage(`❌ **Error:** ${result.error}`, 'assistant');
            }
        } catch (err) {
            console.error("Fetch Error:", err);
            hideTypingIndicator();
            addMessage('❌ **Network Error:** Sorry, there was a problem connecting to the server. Please check your connection and try again.', 'assistant');
        }
    }

    function addMessage(content, sender, useTypewriter = false) {
        const messageRow = document.createElement('div');
        messageRow.className = 'w-full max-w-3xl mx-auto flex mb-8';

        if (sender === 'user') {
            messageRow.classList.add('justify-end');
            const messageBubble = document.createElement('div');
            messageBubble.className = 'bg-[#1c1c1c] text-gray-200 font-semibold p-4 rounded-xl max-w-xl';
            messageBubble.innerHTML = formatContent(content);
            messageRow.appendChild(messageBubble);
        } else { // Assistant
            messageRow.classList.add('justify-start');
            const messageContent = document.createElement('div');
            messageContent.className = 'text-gray-300 w-full message-content';
            
            if (useTypewriter) {
                typeMessage(content, messageContent);
            } else {
                messageContent.innerHTML = formatContent(content);
            }
            messageRow.appendChild(messageContent);
        }
        
        messagesContainer.appendChild(messageRow);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const indicatorRow = document.createElement('div');
        indicatorRow.id = 'typing-indicator';
        indicatorRow.className = 'w-full max-w-3xl mx-auto flex justify-start mb-8';
        indicatorRow.innerHTML = `
            <div class="text-gray-400 flex items-center gap-3">
                <div class="flex items-center justify-center relative" style="width: 32px; height: 32px;">
                    <svg id="spinner" class="spinner absolute" style="width: 32px; height: 32px;" viewBox="0 0 50 50">
                        <defs>
                            <linearGradient id="spinner-gradient"><stop offset="0%" style="stop-color: #25f4ee;"/><stop offset="50%" style="stop-color: #af52de;"/><stop offset="100%" style="stop-color: #ff2d55;"/></linearGradient>
                            <linearGradient id="red-yellow-gradient"><stop offset="0%" style="stop-color: #ff2d55;"/><stop offset="100%" style="stop-color: rgba(255, 149, 0, 0.9);"/></linearGradient>
                            <linearGradient id="green-blue-gradient"><stop offset="0%" style="stop-color: #22c55e;"/><stop offset="100%" style="stop-color: #3b82f6;"/></linearGradient>
                        </defs>
                        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
                    </svg>
                    <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </div>
                <span>Thinking...</span>
            </div>`;
        messagesContainer.appendChild(indicatorRow);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        const spinner = document.getElementById('spinner');
        if (!spinner) return;
        
        const states = ['state-one', 'state-two', 'state-three'];
        let currentStateIndex = 0;
        const animationDuration = 2000; // Duration of one full rotation in ms

        const runAnimationCycle = () => {
            // Remove all possible state classes
            spinner.classList.remove(...states);
            // Add the new current state class
            spinner.classList.add(states[currentStateIndex]);
            
            // Increment index, and loop back to 0 if it reaches the end
            currentStateIndex = (currentStateIndex + 1) % states.length;
            
            // Set timer for the next cycle
            spinnerAnimationTimer = setTimeout(runAnimationCycle, animationDuration);
        };
        
        runAnimationCycle(); // Start the animation loop
    }

    function hideTypingIndicator() {
        if (spinnerAnimationTimer) clearTimeout(spinnerAnimationTimer);
        spinnerAnimationTimer = null;
        document.getElementById('typing-indicator')?.remove();
    }

    function typeMessage(content, element) {
        let i = 0;
        element.innerHTML = "";
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        element.appendChild(cursor);
        function typing() {
            if (i < content.length) {
                element.insertBefore(document.createTextNode(content.charAt(i)), cursor);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                i++;
                setTimeout(typing, 5);
            } else {
                cursor.remove();
                element.innerHTML = formatContent(content); // Re-format to render links, etc.
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
        typing();
    }

    function formatContent(content) {
        // Sanitize first to prevent XSS
        const sanitized = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        // Then apply formatting
        return sanitized
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="font-semibold">$1</a>')
            .replace(/\n/g, '<br>');
    }

    function formatArticleResponse(data) {
        return `**${data.title}**\n\n👤 **Author(s):** ${data.authors}\n📅 **Published:** ${data.publish_date}\n😊 **Sentiment:** ${data.sentiment}\n\n📝 **Summary:**\n${data.summary}\n\n🔗 [Read Original Source](${data.url})`;
    }

    // --- History Management ---
    async function loadHistory() {
        try {
            const response = await fetch('/get-history/');
            const result = await response.json();
            if (!result.success) return;

            historyContainer.innerHTML = '';
            const sections = { 'Today': result.data.today, 'Previous 7 Days': result.data.week, 'Older': result.data.older };
            for (const [title, articles] of Object.entries(sections)) {
                if (articles.length > 0) {
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 px-2 mt-4';
                    titleDiv.textContent = title;
                    historyContainer.appendChild(titleDiv);
                    const ul = document.createElement('ul');
                    ul.className = 'space-y-1';
                    articles.forEach(article => ul.appendChild(createHistoryItem(article)));
                    historyContainer.appendChild(ul);
                }
            }
        } catch (error) { console.error('Error loading history:', error); }
    }

    function createHistoryItem(article) {
        const li = document.createElement('li');
        li.className = 'history-item relative group flex items-center justify-between rounded-md hover:bg-gray-800/60 transition-colors duration-200';
        li.dataset.id = article.id;
        li.innerHTML = `<a href="#" class="flex-grow px-3 py-2 text-sm text-gray-300 truncate">${article.short_title}</a><div class="history-actions absolute right-1 top-1/2 -translate-y-1/2 flex items-center"><button class="delete-history-btn p-2 rounded-md text-gray-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clip-rule="evenodd"></path></svg></button></div>`;
        
        li.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            if (li.classList.contains('bg-gray-700/50')) return;
            setActiveHistoryItem(article.id);
            loadArticle(article.id);
        });

        li.querySelector('.delete-history-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteArticle(article.id, li);
        });

        return li;
    }
    
    function setActiveHistoryItem(articleId) {
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.toggle('bg-gray-700/50', item.dataset.id == articleId);
        });
    }

    async function loadArticle(articleId) {
        welcomeScreen?.classList.add('hidden');
        messagesContainer.innerHTML = '';
        showTypingIndicator();
        try {
            const response = await fetch(`/get-article/${articleId}/`);
            const result = await response.json();
            hideTypingIndicator();
            if (result.success) {
                addMessage(result.data.url, 'user');
                addMessage(formatArticleResponse(result.data), 'assistant', false);
                chatTitle.textContent = result.data.short_title;
            } else { addMessage(`❌ **Error:** ${result.error}`, 'assistant'); }
        } catch (error) {
            hideTypingIndicator();
            addMessage('❌ **Network Error:** Could not load the article.', 'assistant');
        }
    }

    async function deleteArticle(articleId, element) {
        try {
            const response = await fetch(`/delete-article/${articleId}/`, { method: 'DELETE', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
            const result = await response.json();
            if (result.success) {
                if (element.classList.contains('bg-gray-700/50')) newChatBtn.click();
                element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                element.style.opacity = '0';
                element.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    element.remove();
                    // Check if a section is now empty and remove its title
                    const list = element.parentElement;
                    if (list && list.children.length === 0) {
                        list.previousElementSibling?.remove(); // Removes the date title
                        list.remove();
                    }
                }, 300);
            } else {
                // Using a custom modal/alert would be better in a real app
                console.error(`Error deleting article: ${result.error}`);
            }
        } catch (error) {
            console.error('An error occurred while deleting the article.', error);
        }
    }

    // --- Event Listeners & Initial Load ---
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    
    searchToggleBtn.addEventListener('click', () => {
        searchToggleBtn.classList.toggle('search-active');
    });

    newChatBtn.addEventListener('click', () => {
        messagesContainer.innerHTML = '';
        if (welcomeScreen) {
            messagesContainer.appendChild(welcomeScreen);
            welcomeScreen.classList.remove('hidden');
        }
        chatTitle.textContent = 'New Chat';
        document.querySelectorAll('.history-item').forEach(item => item.classList.remove('bg-gray-700/50'));
        messageInput.value = '';
        messageInput.style.height = 'auto';
        messageInput.focus();
        updateSendButtonState();
    });
    
    // Initial setup
    setInitialSidebarState();
    loadHistory();
    messageInput.focus();
    updateSendButtonState();
    window.addEventListener('resize', setInitialSidebarState);
});
