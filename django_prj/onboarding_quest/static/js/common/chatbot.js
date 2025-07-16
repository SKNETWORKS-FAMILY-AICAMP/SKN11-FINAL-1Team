class ChatBot {
    constructor() {
        this.sessionItems = document.querySelectorAll('.chatbot-session-item');
        this.chatArea = document.getElementById('chatbot-chat-area');
        this.selectedSessionInput = document.getElementById('selected-session-id');
        this.deleteModalSessionId = null;
        this.isSubmitting = false;
        this.init();
    }

    init() {
        this.bindEvents();

        // 수정: 이미 선택된 세션이 있는지 확인
        const selectedSession = document.querySelector('.chatbot-session-item.selected');
        if (selectedSession) {
            this.selectSession(selectedSession);
        } else if (this.sessionItems.length > 0) {
            this.selectSession(this.sessionItems[0]);
        }
    }

    bindEvents() {
        this.sessionItems.forEach((item) => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.delete-session-btn')) {
                    return;
                }
                this.handleSessionClick(e, item);
            });
        });

        const chatForm = document.getElementById('chatbot-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleMessageSubmit(e);
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDeleteModal();
            }
        });
    }

    handleSessionClick(e, item) {
        this.selectSession(item);
    }

    selectSession(item) {
        this.sessionItems.forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');

        const sessionId = item.getAttribute('data-session-id');

        if (this.selectedSessionInput) {
            this.selectedSessionInput.value = sessionId;
            console.log('선택된 세션 ID:', sessionId);
        }

        this.loadSessionMessages(sessionId);
    }

    loadSessionMessages(sessionId) {
        const sessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (!sessionItem) return;

        const messageScript = sessionItem.querySelector('.session-messages');
        let messages = [];

        if (messageScript) {
            try {
                messages = JSON.parse(messageScript.textContent);
            } catch (e) {
                console.error('메시지 파싱 오류:', e);
                return;
            }
        }

        this.renderMessages(messages);
    }

    renderMessages(messages) {
        this.chatArea.innerHTML = '';

        if (!messages || messages.length === 0) {
            this.chatArea.innerHTML = '<div class="empty-chat">메시지가 없습니다.</div>';
            return;
        }

        messages.forEach(message => {
            const messageRow = document.createElement('div');
            messageRow.className = `chatbot-msg-row ${message.type === 'user' ? 'user' : 'bot'}`;

            const messageContent = document.createElement('div');
            messageContent.className = `chatbot-msg-${message.type === 'user' ? 'user' : 'chabot'}`;
            messageContent.textContent = message.text;

            messageRow.appendChild(messageContent);
            this.chatArea.appendChild(messageRow);
        });

        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }

    handleMessageSubmit(e) {
        if (this.isSubmitting) return;

        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();

        if (!message) {
            console.log('메시지가 비어있습니다.');
            return;
        }

        this.isSubmitting = true;

        const selectedSessionId = this.selectedSessionInput ? this.selectedSessionInput.value : null;
        console.log('메시지 전송:', message);
        console.log('선택된 세션:', selectedSessionId);

        this.addMessageToChat('user', message);
        this.showLoadingAnimation();

        setTimeout(() => {
            e.target.submit();
        }, 100);
    }

    addMessageToChat(type, text) {
        const messageRow = document.createElement('div');
        messageRow.className = `chatbot-msg-row ${type === 'user' ? 'user' : 'bot'}`;

        const messageContent = document.createElement('div');
        messageContent.className = `chatbot-msg-${type === 'user' ? 'user' : 'chabot'}`;
        messageContent.textContent = text;

        messageRow.appendChild(messageContent);
        this.chatArea.appendChild(messageRow);

        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }

    showLoadingAnimation() {
        const loadingMessage = document.getElementById('loading-message');
        if (loadingMessage) {
            loadingMessage.style.display = 'block';
            this.chatArea.scrollTop = this.chatArea.scrollHeight;
        }
    }

    closeDeleteModal() {
        const modal = document.getElementById('deleteModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.deleteModalSessionId = null;
    }

    async executeDelete(sessionId) {
        try {
            const response = await fetch(`/common/chatbot/session/${sessionId}/delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                window.location.reload();
            } else {
                alert('삭제 실패: ' + (data.error || '알 수 없는 오류'));
            }
        } catch (error) {
            console.error('삭제 요청 오류:', error);
            alert('삭제 중 오류가 발생했습니다.');
        }
    }

    getCsrfToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

// 전역 함수들
function createNewSession() {
    fetch('/common/chatbot/new-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 새로 생성된 세션으로 리다이렉트
                window.location.href = `/common/chatbot/?session=${data.session_id}`;
            } else {
                alert('새 채팅 생성 실패: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('새 채팅 생성 오류:', error);
            alert('새 채팅 생성 중 오류가 발생했습니다.');
        });
}

function deleteSession(element, event) {
    event.stopPropagation();

    const sessionId = element.getAttribute('data-session-id');
    const modal = document.getElementById('deleteModal');

    if (modal) {
        modal.style.display = 'flex';
        if (window.chatBot) {
            window.chatBot.deleteModalSessionId = sessionId;
        }
    }
}

function closeDeleteModal() {
    if (window.chatBot) {
        window.chatBot.closeDeleteModal();
    }
}

function confirmDelete() {
    if (window.chatBot && window.chatBot.deleteModalSessionId) {
        window.chatBot.executeDelete(window.chatBot.deleteModalSessionId);
        closeDeleteModal();
    }
}

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

document.addEventListener('DOMContentLoaded', function () {
    window.chatBot = new ChatBot();
});
