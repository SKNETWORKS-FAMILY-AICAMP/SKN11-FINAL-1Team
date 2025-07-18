class ChatBot {
    constructor() {
        this.chatArea = document.getElementById('chatbot-chat-area');
        this.selectedSessionInput = document.getElementById('selected-session-id');
        this.deleteModalSessionId = null;
        this.isSubmitting = false;
        this.loadingMessageElement = null;
        this.renderLock = false;  // ✅ 메시지 중복 렌더링 방지
        this.refreshSessionList();
    }

    refreshSessionList() {
        this.sessionItems = document.querySelectorAll('.chatbot-session-item');
        this.bindEvents();

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
                if (e.target.closest('.delete-session-btn')) return;
                this.handleSessionClick(e, item);
            });
        });

        const chatForm = document.getElementById('chatbot-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeDeleteModal();
        });
    }

    async handleMessageSubmit(e) {
        e.preventDefault();
        if (this.isSubmitting) return;

        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        if (!message) return;

        this.isSubmitting = true;

        // ✅ 사용자 메시지 즉시 출력 (UX)
        this.addMessageToChat('user', message);

        // ❌ session-messages에는 넣지 않음 (중복 방지)
        // this.updateSessionMessagesInDOM('user', message); ← 이 줄 제거해야 함

        this.showLoadingAnimation();

        const sessionId = this.selectedSessionInput ? this.selectedSessionInput.value : null;

        try {
            const response = await fetch('/common/chatbot/api/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ message, session_id: sessionId })
            });

            const data = await response.json();
            if (data.success) {
                this.selectedSessionInput.value = data.session_id;

                // ✅ 응답을 기존 자리에 타자 애니메이션으로 출력
                if (this.loadingMessageElement) {
                    await this.typeText(this.loadingMessageElement, data.answer);
                    this.loadingMessageElement.parentElement.classList.remove('loading');
                    this.loadingMessageElement = null;
                }

                // ✅ session-messages에 챗봇 메시지만 동기화
                this.updateSessionMessagesInDOM('chatbot', data.answer);
            } else {
                alert('오류: ' + data.error);
            }
        } catch (err) {
            console.error('에러 발생:', err);
            alert('메시지 전송 중 오류가 발생했습니다.');
        }

        input.value = '';
        this.isSubmitting = false;
    }


    showLoadingAnimation() {
        const oldLoading = document.querySelector('.chatbot-msg-row.bot.loading');
        if (oldLoading) oldLoading.remove();

        const messageRow = document.createElement('div');
        messageRow.className = 'chatbot-msg-row bot loading';

        const messageContent = document.createElement('div');
        messageContent.className = 'chatbot-msg-chabot loading';
        messageContent.innerHTML = `
            <div class="loading-wave">
                <span style="--i:0">답</span><span style="--i:1">변</span><span style="--i:2">을</span><span style="--i:3">&nbsp;</span>
                <span style="--i:4">생</span><span style="--i:5">성</span><span style="--i:6">하</span><span style="--i:7">고</span>
                <span style="--i:8">&nbsp;</span><span style="--i:9">있</span><span style="--i:10">습</span><span style="--i:11">니</span>
                <span style="--i:12">다</span><span style="--i:13">.</span><span style="--i:14">.</span><span style="--i:15">.</span>
            </div>
        `;

        messageRow.appendChild(messageContent);
        this.chatArea.appendChild(messageRow);
        this.chatArea.scrollTop = this.chatArea.scrollHeight;

        this.loadingMessageElement = messageContent;
    }

    async typeText(element, text) {
        element.innerHTML = '';
        for (let i = 0; i < text.length; i++) {
            element.textContent += text[i];
            this.chatArea.scrollTop = this.chatArea.scrollHeight;
            await new Promise(res => setTimeout(res, 15));
        }
    }

    updateSessionMessagesInDOM(type, text) {
        const sessionId = this.selectedSessionInput.value;
        const sessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (!sessionItem) return;

        const script = sessionItem.querySelector('.session-messages');
        if (!script) return;

        try {
            const existing = JSON.parse(script.textContent);
            existing.push({
                type: type,
                text: text,
                time: new Date().toISOString().split('T')[0]
            });
            script.textContent = JSON.stringify(existing);
        } catch (e) {
            console.error('session-messages 업데이트 실패:', e);
        }
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
        if (this.renderLock) return;
        this.renderLock = true;  // ✅ 중복 렌더링 방지

        console.log("✅ renderMessages 실행됨", messages);

        this.chatArea.innerHTML = '';
        if (!messages || messages.length === 0) {
            this.chatArea.innerHTML = '<div class="empty-chat">메시지가 없습니다.</div>';
            this.renderLock = false;
            return;
        }

        messages.forEach(message => {
            this.addMessageToChat(message.type === 'user' ? 'user' : 'bot', message.text);
        });

        this.renderLock = false;
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

    closeDeleteModal() {
        const modal = document.getElementById('deleteModal');
        if (modal) modal.style.display = 'none';
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
    if (!window.chatBot) {
        window.chatBot = new ChatBot();  // ✅ 한 번만 실행되도록 보장
    }
});
