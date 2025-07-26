const user_id = window.user_id;
const department_id = window.department_id;

class ChatBot {
    constructor() {
        // DOM 요소들이 존재하는지 확인 후 초기화
        this.chatArea = document.getElementById('chatbot-chat-area');
        this.selectedSessionInput = document.getElementById('selected-session-id');
        
        if (!this.chatArea || !this.selectedSessionInput) {
            console.error('필수 DOM 요소를 찾을 수 없습니다:', {
                chatArea: !!this.chatArea,
                selectedSessionInput: !!this.selectedSessionInput
            });
            return;
        }
        
        this.deleteModalSessionId = null;
        this.isSubmitting = false;
        this.loadingMessageElement = null;
        this.renderLock = false;  // ✅ 메시지 중복 렌더링 방지
        this.userScrolling = false;
        
        this.bindEvents();  // 이벤트 바인딩
        this.loadSessionsFromAPI();  // ✅ 기존 refreshSessionList() 대신

    }

    async loadMessagesFromAPI(sessionId) {
        try {
            const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/messages/${sessionId}`);
            const data = await res.json();

            if (!data.success) {
                alert("메시지를 불러오는 데 실패했습니다.");
                return;
            }

            this.selectedSessionInput.value = sessionId;
            this.chatArea.innerHTML = '';

            data.messages.forEach(msg => {
                const msgDiv = document.createElement("div");
                msgDiv.classList.add("chatbot-message", msg.type === "user" ? "user" : "bot");

                const textDiv = document.createElement("div");
                textDiv.className = "chatbot-message-text";
                textDiv.innerText = msg.text;

                msgDiv.appendChild(textDiv);
                this.chatArea.appendChild(msgDiv);
            });

            this.scrollToBottom();
        } catch (e) {
            console.error("메시지 로딩 오류:", e);
            alert("메시지 로딩 중 오류 발생");
        }
    }


    async loadSessionsFromAPI() {
        console.log("📥 세션 로드 시작");

        try {
            const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/sessions/${user_id}`);
            const data = await res.json();

            console.log("📥 세션 목록 응답 데이터:", data);

            if (!data.success) {
                alert("세션 목록을 불러오는 데 실패했습니다.");
                return;
            }

            const listContainer = document.getElementById("chatbot-session-list");
            if (!listContainer) {
                console.warn("❗ #chatbot-session-list 요소가 없음");
                return;
            }

            listContainer.innerHTML = '';

            data.sessions.forEach(session => {
                console.log("📄 세션 추가됨:", session.session_id, session.summary);  // ✅ 개별 세션 확인용

                const div = document.createElement("div");
                div.className = "chatbot-session-item";
                div.setAttribute("data-session-id", session.session_id);
                div.innerHTML = `
                <div class="chatbot-session-title">
  <span class="chat-icon">💬</span>
  <span class="session-summary">${session.summary || "새 대화"}</span>
</div>
                <div class="chatbot-session-preview">${session.preview || "..."}</div>
                <button class="delete-session-btn" data-session-id="${session.session_id}">×</button>
                <script type="application/json" class="session-messages">[]</script>
            `;
                listContainer.appendChild(div);
            });

            this.refreshSessionList();
            this.sessionItems = document.querySelectorAll('.chatbot-session-item');
            this.sessionItems.forEach((item) => {
                item.addEventListener('click', (e) => {
                    if (e.target.closest('.delete-session-btn')) return;
                    this.handleSessionClick(e, item);
                });

                const chatbot = this;
                const deleteBtn = item.querySelector('.delete-session-btn');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const sessionId = deleteBtn.getAttribute("data-session-id");
                        chatbot.openDeleteModal(sessionId);
                    });
                }
            });

            console.log("✅ 세션 목록 렌더링 완료");

        } catch (e) {
            console.error("세션 목록 로딩 오류:", e);
            alert("세션 목록을 불러오는 중 오류가 발생했습니다.");
        }
    }



    refreshSessionList() {
        this.sessionItems = document.querySelectorAll('.chatbot-session-item');
        this.bindEvents();

        const selectedSession = document.querySelector('.chatbot-session-item.selected');
        if (selectedSession) {
            this.selectSession(selectedSession);
        } else if (this.sessionItems && this.sessionItems.length > 0) {
            this.selectSession(this.sessionItems[0]);
        }
    }

    bindEvents() {
        if (!this.sessionItems) return;
        
        this.sessionItems.forEach((item) => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.delete-session-btn')) return;
                this.handleSessionClick(e, item);
            });
        });

        this.chatArea.addEventListener('scroll', () => {
            const nearBottom = this.chatArea.scrollHeight - this.chatArea.scrollTop - this.chatArea.clientHeight < 30;
            this.userScrolling = !nearBottom;
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

        const sendBtn = document.querySelector('.chatbot-send-btn');
        const btnText = sendBtn?.querySelector('.btn-text');
        const btnLoading = sendBtn?.querySelector('.btn-loading');

        console.log('📤 메시지 제출됨:', message);

        this.isSubmitting = true;

        // ✅ 전송 버튼 로딩 표시
        if (btnText && btnLoading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline-flex';
            sendBtn.disabled = true;
            input.disabled = true;
        }

        input.value = '';

        this.addMessageToChat('user', message);
        this.showLoadingAnimation();

        const sessionId = this.selectedSessionInput ? this.selectedSessionInput.value : null;

        try {
            const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/rag`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: message,
                    session_id: sessionId ? parseInt(sessionId) : null,
                    user_id: parseInt(user_id),
                    department_id: parseInt(department_id)
                })
            });

            const data = await response.json();
            if (data.success) {
                this.selectedSessionInput.value = data.session_id;

                if (this.loadingMessageElement) {
                    await this.typeText(this.loadingMessageElement, data.answer);
                    this.loadingMessageElement.parentElement.classList.remove('loading');
                    this.loadingMessageElement = null;
                }

                if (data.contexts && data.contexts.length > 0) {
                    const sourcesText = `\n\n📚 참고 문서: ${data.contexts.length}개 문서 참조`;
                    const sourcesSpan = document.createElement('span');
                    sourcesSpan.style.fontSize = '12px';
                    sourcesSpan.style.color = '#666';
                    sourcesSpan.textContent = sourcesText;
                    this.loadingMessageElement?.parentElement.appendChild(sourcesSpan);
                }

                this.updateSessionMessagesInDOM('chatbot', data.answer);
            } else {
                alert('오류: ' + (data.error || data.detail || '알 수 없는 오류'));
            }
        } catch (err) {
            console.error('에러 발생:', err);
            alert('메시지 전송 중 오류가 발생했습니다.');
        }

        // ✅ 전송 버튼 상태 복원
        if (btnText && btnLoading) {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            sendBtn.disabled = false;
            input.disabled = false;
            input.focus();
        }

        this.isSubmitting = false;
    }



    // async handleMessageSubmit(e) {
    //     e.preventDefault();
    //     if (this.isSubmitting) return;

    //     const input = document.getElementById('chatbot-input');
    //     const message = input.value.trim();
    //     if (!message) return;

    //     console.log('📤 메시지 제출됨:', message);

    //     this.isSubmitting = true;

    //     input.value = '';

    //     // ✅ 사용자 메시지 즉시 출력 (UX)
    //     this.addMessageToChat('user', message);



    //     this.showLoadingAnimation();

    //     const sessionId = this.selectedSessionInput ? this.selectedSessionInput.value : null;

    //     try {
    //         const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/rag`, {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json'
    //             },
    //             body: JSON.stringify({
    //                 question: message,
    //                 session_id: sessionId ? parseInt(sessionId) : null,
    //                 user_id: parseInt(user_id),
    //                 department_id: parseInt(department_id)
    //             })
    //         });

    //         const data = await response.json();
    //         if (data.success) {
    //             this.selectedSessionInput.value = data.session_id;

    //             // ✅ 응답을 기존 자리에 타자 애니메이션으로 출력
    //             if (this.loadingMessageElement) {
    //                 await this.typeText(this.loadingMessageElement, data.answer);
    //                 this.loadingMessageElement.parentElement.classList.remove('loading');
    //                 this.loadingMessageElement = null;
    //             }

    //             // ✅ 소스 정보 표시 (선택사항)
    //             if (data.contexts && data.contexts.length > 0) {
    //                 const sourcesText = `\n\n📚 참고 문서: ${data.contexts.length}개 문서 참조`;
    //                 const sourcesSpan = document.createElement('span');
    //                 sourcesSpan.style.fontSize = '12px';
    //                 sourcesSpan.style.color = '#666';
    //                 sourcesSpan.textContent = sourcesText;
    //                 this.loadingMessageElement?.parentElement.appendChild(sourcesSpan);
    //             }

    //             // ✅ session-messages에 챗봇 메시지만 동기화
    //             this.updateSessionMessagesInDOM('chatbot', data.answer);
    //         } else {
    //             alert('오류: ' + (data.error || data.detail || '알 수 없는 오류'));
    //         }
    //     } catch (err) {
    //         console.error('에러 발생:', err);
    //         alert('메시지 전송 중 오류가 발생했습니다.');
    //     }

    //     // input.value = '';
    //     this.isSubmitting = false;
    // }


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

    // async typeText(element, text) {
    //     element.innerHTML = '';
    //     for (let i = 0; i < text.length; i++) {
    //         element.textContent += text[i];
    //         this.chatArea.scrollTop = this.chatArea.scrollHeight;
    //         await new Promise(res => setTimeout(res, 15));
    //     }
    // }
    // async typeText(element, text) {
    //     const converter = new showdown.Converter({
    //         simpleLineBreaks: true,
    //         tables: true
    //     });

    //     let currentText = '';
    //     for (let i = 0; i < text.length; i++) {
    //         currentText += text[i];

    //         // 실시간으로 Markdown 변환 및 렌더링
    //         element.innerHTML = converter.makeHtml(currentText);

    //         // 스크롤을 자동으로 가장 아래로 이동
    //         this.chatArea.scrollTop = this.chatArea.scrollHeight;

    //         // 글자 출력 속도 조절 (15ms마다 1글자씩 출력)
    //         await new Promise(res => setTimeout(res, 15));
    //     }
    // }
    async typeText(element, fullText, speed = 15) {
        const converter = new showdown.Converter({
            simpleLineBreaks: true,
            tables: true
        });

        let i = 0;
        let currentText = '';
        const total = fullText.length;
        const start = performance.now();

        const loop = (now) => {
            const elapsed = now - start;
            const expectedChars = Math.floor(elapsed / speed);

            while (i < expectedChars && i < total) {
                currentText += fullText[i];
                i++;
            }

            element.innerHTML = converter.makeHtml(currentText);
            // this.chatArea.scrollTop = this.chatArea.scrollHeight;
            if (!this.userScrolling) {
                this.chatArea.scrollTop = this.chatArea.scrollHeight;
            }

            if (i < total) {
                requestAnimationFrame(loop);
            }
        };

        requestAnimationFrame(loop);
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
        if (this.isSubmitting) {
            this.isSubmitting = false;
            this.loadingMessageElement = null;

            const loadingRow = this.chatArea.querySelector('.chatbot-msg-row.bot.loading');
            if (loadingRow) loadingRow.remove();
        }
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

    async loadSessionMessages(sessionId) {
        try {
            const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/messages/${sessionId}`);
            const data = await res.json();

            if (!data.success) {
                alert("메시지를 불러오는 데 실패했습니다.");
                return;
            }

            this.renderMessages(data.messages);
        } catch (err) {
            console.error("메시지 불러오기 실패:", err);
            alert("메시지 로딩 중 오류 발생");
        }
    }

    renderMessages(messages) {
        console.log("📥 렌더링할 메시지:", messages);  // 추가
        if (this.renderLock) return;
        this.renderLock = true;

        this.chatArea.innerHTML = '';

        if (!messages || messages.length === 0) {
            this.chatArea.innerHTML = '<div class="empty-chat">메시지가 없습니다.</div>';
            this.renderLock = false;
            return;
        }

        // ✅ 타입 정규화 및 순서대로 렌더링
    messages.forEach(message => {
        // 타입 정규화 처리
        let messageType = 'bot'; // 기본값
        if (message.type === 'user') {
            messageType = 'user';
        } else if (message.type === 'chatbot' || message.type === 'bot') {
            messageType = 'bot';
        }
        
        console.log(`렌더링: ${messageType} - ${message.text.substring(0, 50)}...`);
        this.addMessageToChat(messageType, message.text);
    });

        // ✅ 항상 아래로 스크롤
        this.chatArea.scrollTop = this.chatArea.scrollHeight;

        this.renderLock = false;
    }


    addMessageToChat(type, text) {
        const messageRow = document.createElement('div');
        messageRow.className = `chatbot-msg-row ${type === 'user' ? 'user' : 'bot'}`;

        const messageContent = document.createElement('div');
        messageContent.className = `chatbot-msg-${type === 'user' ? 'user' : 'chabot'}`;

        if (type === 'bot') {
            const converter = new showdown.Converter({
                simpleLineBreaks: true,
                tables: true
            });

            // 📌 참고 문서 앞에 줄 바꿈 추가
            const patchedText = text.replace(/(📄 참고 문서:)/g, "<br>$1");
            const html = converter.makeHtml(patchedText);
            messageContent.innerHTML = html;

            // ✅ 한 줄짜리 응답이면 single-line 스타일 적용
            const lineCount = (html.match(/<p>/g) || []).length;
            const isList = html.includes('<ul') || html.includes('<ol');
            const hasBreaks = html.includes('<br');

            if (lineCount <= 1 && !isList && !hasBreaks) {
                messageContent.classList.add('single-line');
            }
        } else {
            messageContent.textContent = text;
        }

        messageRow.appendChild(messageContent);
        this.chatArea.appendChild(messageRow);

        if (!this.userScrolling) {
            this.chatArea.scrollTop = this.chatArea.scrollHeight;
        }
    }


    // addMessageToChat(type, text) {
    //     const messageRow = document.createElement('div');
    //     messageRow.className = `chatbot-msg-row ${type === 'user' ? 'user' : 'bot'}`;

    //     const messageContent = document.createElement('div');
    //     messageContent.className = `chatbot-msg-${type === 'user' ? 'user' : 'chabot'}`;

    //     if (type === 'bot') {
    //         const converter = new showdown.Converter({
    //             simpleLineBreaks: true,
    //             tables: true
    //         });

    //         // 📌 📄 참고 문서 앞에 두 줄 띄우기 (전처리)
    //         // const patchedText = text.replace(/\n{1}(📄 참고 문서:)/g, "\n\n$1");
    //         // const patchedText = text.replace(/(📄 참고 문서:)/g, "\n\n$1");
    //         const patchedText = text.replace(/(📄 참고 문서:)/g, "<br>$1");


    //         const html = converter.makeHtml(patchedText);
    //         messageContent.innerHTML = html;

            
    //     } else {
    //         messageContent.textContent = text;
    //     }

    //     messageRow.appendChild(messageContent);
    //     this.chatArea.appendChild(messageRow);
    //     // this.chatArea.scrollTop = this.chatArea.scrollHeight;
    //     if (!this.userScrolling) {
    //         this.chatArea.scrollTop = this.chatArea.scrollHeight;
    //     }

    // }




    closeDeleteModal() {
        const modal = document.getElementById('deleteModal');
        if (modal) modal.style.display = 'none';
        this.deleteModalSessionId = null;
    }

    openDeleteModal(sessionId) {
        const modal = document.getElementById('deleteModal');
        if (modal) modal.style.display = 'flex';
        this.deleteModalSessionId = sessionId;
    }

    async executeDelete() {
        try {
            const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/session/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    session_id: this.deleteModalSessionId,
                    user_id: user_id
                })
            });

            const data = await response.json();
            if (data.success) {
                this.closeDeleteModal();

                // ✅ 선택된 세션이 삭제된 세션이면 UI 초기화
                if (this.selectedSessionInput.value === this.deleteModalSessionId) {
                    this.selectedSessionInput.value = '';
                    this.chatArea.innerHTML = '';
                    document.getElementById("chatbot-input").value = '';
                }

                // ✅ 목록 다시 불러오고 이벤트 다시 붙이기
                await this.loadSessionsFromAPI();
            } else {
                alert("삭제 실패: " + (data.error || ""));
            }
        } catch (error) {
            console.error("삭제 오류:", error);
            alert("삭제 중 오류 발생");
        }
    }



    getCsrfToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

async function createNewSession() {
    try {
        const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/session/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ user_id: user_id })
        });

        const data = await res.json();
        if (!data.success) {
            alert("세션 생성 실패: " + (data.error || ""));
            return;
        }

        const listContainer = document.getElementById("chatbot-session-list");

        // ✅ 새 세션 DOM 직접 생성해서 추가
        const div = document.createElement("div");
        div.className = "chatbot-session-item selected";
        div.setAttribute("data-session-id", data.session_id);
        div.innerHTML = `
  <div class="chatbot-session-title">
    <span class="chat-icon">💬</span>
    <span class="session-summary">새 대화</span>
  </div>
  <div class="chatbot-session-preview">...</div>
  <button class="delete-session-btn" data-session-id="${data.session_id}">×</button>
  <script type="application/json" class="session-messages">[]</script>
`;

        // ✅ 기존 selected 제거
        document.querySelectorAll('.chatbot-session-item.selected')
            .forEach(el => el.classList.remove('selected'));

        listContainer.prepend(div);

        // ✅ 세션 입력값 초기화
        window.chatBot.selectedSessionInput.value = data.session_id;
        window.chatBot.chatArea.innerHTML = '';
        document.getElementById("chatbot-input").value = '';

        // ✅ 클릭 이벤트 바인딩
        div.addEventListener('click', (e) => {
            if (e.target.closest('.delete-session-btn')) return;
            window.chatBot.selectSession(div);
        });

        const deleteBtn = div.querySelector('.delete-session-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                window.chatBot.openDeleteModal(data.session_id);
            });
        }

        // 🔥 추가: 챗봇 환영 메시지 자동 출력
        const welcomeText = "어서오세요. 무엇을 도와드릴까요?";
        window.chatBot.addMessageToChat('bot', welcomeText);

        // 🔥 추가: session-messages 스크립트에도 초기 메시지 반영
        const script = div.querySelector('.session-messages');
        if (script) {
            try {
                const existing = JSON.parse(script.textContent || '[]');
                existing.push({
                    type: 'bot',
                    text: welcomeText,
                    time: new Date().toISOString().split('T')[0]
                });
                script.textContent = JSON.stringify(existing);
            } catch (e) {
                console.error('세션 메시지 초기화 실패:', e);
            }
        }

    } catch (e) {
        console.error("세션 생성 실패:", e);
        alert("세션 생성 중 오류가 발생했습니다.");
    }
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


