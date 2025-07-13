class ChatBot {
    constructor() {
        this.sessionItems = document.querySelectorAll('.chatbot-session-item');
        this.chatArea = document.getElementById('chatbot-chat-area');
        this.init();
    }

    init() {
        this.bindEvents();
        // 첫 번째 세션이 있으면 자동 선택
        if (this.sessionItems.length > 0) {
            this.sessionItems[0].click();
        }
    }

    bindEvents() {
        this.sessionItems.forEach((item) => {
            item.addEventListener('click', (e) => this.handleSessionClick(e, item));
        });
    }

    handleSessionClick(e, item) {
        // 모든 세션 아이템에서 selected 클래스 제거
        this.sessionItems.forEach(i => i.classList.remove('selected'));
        
        // 클릭된 아이템에 selected 클래스 추가
        item.classList.add('selected');
        
        // 해당 세션의 메시지들을 가져와서 표시
        const sessionId = item.getAttribute('data-session-id');
        this.loadSessionMessages(sessionId);
    }

    loadSessionMessages(sessionId) {
        // 세션 아이템에서 메시지 데이터 가져오기
        const sessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (!sessionItem) return;

        const messagesJson = sessionItem.getAttribute('data-messages');
        let messages = [];
        
        try {
            messages = JSON.parse(messagesJson);
        } catch (e) {
            console.error('메시지 파싱 오류:', e);
            return;
        }

        this.renderMessages(messages);
    }

    renderMessages(messages) {
        // 채팅 영역 초기화
        this.chatArea.innerHTML = '';

        if (messages.length === 0) {
            this.chatArea.innerHTML = '<div class="empty-chat">메시지가 없습니다.</div>';
            return;
        }

        // 메시지들을 순서대로 렌더링
        messages.forEach(message => {
            this.createMessageElement(message);
        });

        // 채팅 영역을 맨 아래로 스크롤
        this.scrollToBottom();
    }

    createMessageElement(message) {
        const msgRow = document.createElement('div');
        msgRow.className = 'chatbot-msg-row';
        
        const msgElement = document.createElement('div');
        msgElement.textContent = message.text;

        if (message.type === 'user') {
            msgRow.classList.add('user');
            msgElement.className = 'chatbot-msg-user';
        } else {
            msgElement.className = 'chatbot-msg-bot';
        }

        msgRow.appendChild(msgElement);
        this.chatArea.appendChild(msgRow);
    }

    scrollToBottom() {
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }

    // 새 메시지 추가 (실시간 채팅 시 사용)
    addMessage(text, type) {
        const message = { text, type };
        this.createMessageElement(message);
        this.scrollToBottom();
    }
}

// DOM이 로드되면 ChatBot 인스턴스 생성
document.addEventListener('DOMContentLoaded', function() {
    new ChatBot();
});
