const user_id = window.user_id;
const department_id = window.department_id;

class ChatBot {
    constructor() {
        this.apiBaseUrl = window.api_base_url || 'http://127.0.0.1:8001/api';  // ✅ 추가
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
        this.savedRange = null;
        this.activeAutocompleteIndex = -1;  // ✅ 추가
        this.deleteModalSessionId = null;
        this.isSubmitting = false;
        this.loadingMessageElement = null;
        this.renderLock = false;  // ✅ 메시지 중복 렌더링 방지
        this.userScrolling = false;
        this.autocompleteInput = document.getElementById('chatbot-input');
        this.autocompleteDropdown = document.getElementById('autocomplete-dropdown');
        if (this.autocompleteInput) {
            this.autocompleteInput.addEventListener('input', (e) => this.handleAutocomplete(e));
            this.autocompleteInput.addEventListener('keyup', (e) => this.handleAutocomplete(e)); // ✅ 추가
            // this.autocompleteInput.addEventListener('keydown', (e) => this.handleBackspaceOnToken(e)); // ⬅️ 추가
            this.autocompleteInput.addEventListener('keydown', (e) => {
                this.handleBackspaceOnToken(e);

                const items = this.autocompleteDropdown.querySelectorAll('.autocomplete-dropdown-item');
                if (items.length === 0 || this.autocompleteDropdown.style.display === 'none') return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.activeAutocompleteIndex = (this.activeAutocompleteIndex + 1) % items.length;
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.activeAutocompleteIndex = (this.activeAutocompleteIndex - 1 + items.length) % items.length;
                } else if (e.key === 'Tab' || e.key === 'Enter') {  // ✅ 여기에 Enter도 같이 체크
                    e.preventDefault();
                    if (this.activeAutocompleteIndex >= 0 && this.activeAutocompleteIndex < items.length) {
                        const selected = items[this.activeAutocompleteIndex];
                        this.insertDocumentToken(selected.textContent.trim());
                        this.autocompleteDropdown.style.display = 'none';
                        this.activeAutocompleteIndex = -1;
                    }
                }

                // ✅ 스타일 반영
                items.forEach((el, idx) => {
                    el.classList.toggle('active', idx === this.activeAutocompleteIndex);
                });
            });


        }
    }

    handleBackspaceOnToken(e) {
        if (e.key !== 'Backspace') return;

        const selection = window.getSelection();
        if (!selection.rangeCount) return;

        const range = selection.getRangeAt(0);
        const node = range.startContainer;

        // 커서가 텍스트 노드의 맨 앞에 있고 바로 앞에 토큰이 있을 때
        if (range.collapsed && node.nodeType === 3 && range.startOffset === 0) {
            const prev = node.previousSibling;
            if (prev && prev.classList && prev.classList.contains('token')) {
                prev.remove();
                e.preventDefault();
            }
        }

        // 커서가 토큰 바로 뒤에 위치한 경우 (토큰 다음에 텍스트 노드가 없을 때)
        if (range.collapsed && node.nodeType === 1 && node.previousSibling && node.previousSibling.classList?.contains('token')) {
            node.previousSibling.remove();
            e.preventDefault();
        }
    }


    async loadMessagesFromAPI(sessionId) {
        try {
            // const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/messages/${sessionId}`);
            // const res = await fetch(`${window.api_base_url}/chat/messages/${sessionId}`);
            const res = await fetch(`${window.api_base_url}/chat/messages/${sessionId}`);


            const data = await res.json();

            if (!data.success) {
                showError("메시지를 불러오는 데 실패했습니다.");
                return;
            }

            this.selectedSessionInput.value = sessionId;
            this.chatArea.innerHTML = '';

            data.messages.forEach(msg => {
                const msgDiv = document.createElement("div");
                msgDiv.classList.add("chatbot-message", msg.type === "user" ? "user" : "bot");

                const textDiv = document.createElement("div");
                textDiv.className = "chatbot-message-text";
                // textDiv.innerText = msg.text;
                textDiv.innerHTML = this.reconstructUserMessageWithTokens(msg.text);


                msgDiv.appendChild(textDiv);
                this.chatArea.appendChild(msgDiv);
            });

            this.scrollToBottom();
        } catch (e) {
            console.error("메시지 로딩 오류:", e);
            showError("메시지 로딩 중 오류 발생");
        }
    }


    async loadSessionsFromAPI() {
        console.log("📥 세션 로드 시작");

        try {
            const res = await fetch(`${window.api_base_url}/chat/sessions/${user_id}`);
            const data = await res.json();

            console.log("📥 세션 목록 응답 데이터:", data);

            if (!data.success) {
                showError("세션 목록을 불러오는 데 실패했습니다.");
                return;
            }

            const listContainer = document.getElementById("chatbot-session-list");
            if (!listContainer) {
                console.warn("❗ #chatbot-session-list 요소가 없음");
                return;
            }

            listContainer.innerHTML = '';

            data.sessions.forEach(session => {
                console.log("📄 세션 추가됨:", session.session_id, session.summary);

                const div = document.createElement("div");
                div.className = "chatbot-session-item";
                div.setAttribute("data-session-id", session.session_id);

                // ✅ preview에서 <span ...>...</span> 제거 및 escape 처리
                let cleanPreview = session.preview || "...";
                const temp = document.createElement("textarea");
                temp.innerHTML = cleanPreview;
                cleanPreview = temp.value;
                cleanPreview = cleanPreview.replace(/<span[^>]*?>.*?<\/span>/g, '').trim();
                cleanPreview = cleanPreview
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

                div.innerHTML = `
                <div class="chatbot-session-title">
                    <span class="chat-icon">💬</span>
                    <span class="session-summary">${session.summary || "새 대화"}</span>
                </div>
                <div class="chatbot-session-preview">${cleanPreview}</div>
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
            showError("세션 목록을 불러오는 중 오류가 발생했습니다.");
        }
    }



//     async loadSessionsFromAPI() {
//         console.log("📥 세션 로드 시작");

//         try {
//             // const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/sessions/${user_id}`);
//             // const res = await fetch(`${window.api_base_url}/chat/sessions/${user_id}`);
//             const res = await fetch(`${window.api_base_url}/chat/sessions/${user_id}`);


//             const data = await res.json();

//             console.log("📥 세션 목록 응답 데이터:", data);

//             if (!data.success) {
//                 showError("세션 목록을 불러오는 데 실패했습니다.");
//                 return;
//             }

//             const listContainer = document.getElementById("chatbot-session-list");
//             if (!listContainer) {
//                 console.warn("❗ #chatbot-session-list 요소가 없음");
//                 return;
//             }

//             listContainer.innerHTML = '';

//             data.sessions.forEach(session => {
//                 console.log("📄 세션 추가됨:", session.session_id, session.summary);  // ✅ 개별 세션 확인용

//                 const div = document.createElement("div");
//                 div.className = "chatbot-session-item";
//                 div.setAttribute("data-session-id", session.session_id);
//                 div.innerHTML = `
//                 <div class="chatbot-session-title">
//   <span class="chat-icon">💬</span>
//   <span class="session-summary">${session.summary || "새 대화"}</span>
// </div>
//                 <div class="chatbot-session-preview">${session.preview || "..."}</div>
//                 <button class="delete-session-btn" data-session-id="${session.session_id}">×</button>
//                 <script type="application/json" class="session-messages">[]</script>
//             `;
//                 listContainer.appendChild(div);
//             });

//             this.refreshSessionList();
//             this.sessionItems = document.querySelectorAll('.chatbot-session-item');
//             this.sessionItems.forEach((item) => {
//                 item.addEventListener('click', (e) => {
//                     if (e.target.closest('.delete-session-btn')) return;
//                     this.handleSessionClick(e, item);
//                 });

//                 const chatbot = this;
//                 const deleteBtn = item.querySelector('.delete-session-btn');
//                 if (deleteBtn) {
//                     deleteBtn.addEventListener('click', (e) => {
//                         e.stopPropagation();
//                         const sessionId = deleteBtn.getAttribute("data-session-id");
//                         chatbot.openDeleteModal(sessionId);
//                     });
//                 }
//             });

//             console.log("✅ 세션 목록 렌더링 완료");

//         } catch (e) {
//             console.error("세션 목록 로딩 오류:", e);
//             showError("세션 목록을 불러오는 중 오류가 발생했습니다.");
//         }
//     }


    getCaretText(element) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return '';
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(element);
        preCaretRange.setEnd(range.endContainer, range.endOffset);
        return preCaretRange.toString();
    }



    insertDocumentToken(docName) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        const range = selection.getRangeAt(0);

        // '@검색어' 제거
        const caretText = this.getCaretText(this.autocompleteInput);
        // const match = caretText.match(/@(\S{1,20})$/);
        // if (match) {
        //     const startOffset = range.endOffset - match[0].length;
        //     range.setStart(range.endContainer, startOffset);
        //     range.deleteContents();
        // }
        // '@검색어' 제거
        const match = caretText.match(/@(\S{1,20})$/);
        if (match) {
            const fullMatch = match[0];
            const selection = window.getSelection();
            if (!selection.rangeCount) return;
            const range = selection.getRangeAt(0);

            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(this.autocompleteInput);
            const caretText = preCaretRange.toString();
            const index = caretText.lastIndexOf(fullMatch);

            if (index !== -1) {
                // 전체 텍스트 기준으로 위치 찾아서 삭제 범위 지정
                const allNodes = this.autocompleteInput.childNodes;
                let count = 0;

                for (const node of allNodes) {
                    const nodeText = node.textContent || '';
                    const nextCount = count + nodeText.length;

                    if (index >= count && index < nextCount) {
                        const startOffset = index - count;
                        const endOffset = startOffset + fullMatch.length;

                        const deletionRange = document.createRange();
                        deletionRange.setStart(node, startOffset);
                        deletionRange.setEnd(node, endOffset);
                        deletionRange.deleteContents();

                        // 커서 위치 재조정
                        const newRange = document.createRange();
                        newRange.setStart(node, startOffset);
                        newRange.collapse(true);
                        selection.removeAllRanges();
                        selection.addRange(newRange);
                        break;
                    }

                    count = nextCount;
                }
            }
        }


        // 토큰 <span> 생성
        // const span = document.createElement('span');
        // span.className = 'token';
        // span.textContent = docName;
        // span.contentEditable = 'false';
        // span.style.background = '#e9ecef';
        // span.style.padding = '3px 8px';
        // span.style.margin = '0 4px';
        // span.style.borderRadius = '10px';
        // span.style.fontWeight = '500';
        // span.style.display = 'inline-block';
        // span.style.userSelect = 'none';


        // 문서명 텍스트
        const textSpan = document.createElement('span');
        textSpan.textContent = docName;
        textSpan.style.marginRight = '6px';

        // 삭제 버튼
        const closeBtn = document.createElement('span');
        closeBtn.textContent = '×';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.color = '#999';
        closeBtn.style.marginLeft = '4px';
        closeBtn.style.fontWeight = 'bold';
        closeBtn.addEventListener('click', () => span.remove());

        // 최종 span 조립
        const span = document.createElement('span');
        span.className = 'token';
        span.contentEditable = 'false';
        span.style.display = 'inline-flex';
        span.style.alignItems = 'center';
        span.style.gap = '4px';
        span.style.userSelect = 'none';

        span.appendChild(textSpan);
        span.appendChild(closeBtn);


        // 삽입
        range.insertNode(span);

        // 커서 위치 재조정
        const space = document.createTextNode(' ');
        span.after(space);
        range.setStartAfter(space);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
    }





    handleAutocomplete(e) {
        console.log('[autocomplete triggered]', e);
        const caretText = this.getCaretText(this.autocompleteInput);
        console.log('[caretText]', caretText);
        const match = caretText.match(/@(\S{1,20})$/);
        console.log('[match]', match);
        if (!match) {
            this.autocompleteDropdown.style.display = 'none';
            return;
        }

        const keyword = match[1];

        // fetch(`${this.apiBaseUrl}/chat/autocomplete?query=${encodeURIComponent(keyword)}`)
        fetch(`${this.apiBaseUrl}/chat/autocomplete?query=${encodeURIComponent(keyword)}&user_id=${encodeURIComponent(user_id)}`)



            .then(res => {
                console.log('[autocomplete API response]', res);
                return res.json();
            })
            .then(data => {
                console.log('[autocomplete data]', data);  // ← 이거 추가
                if (!Array.isArray(data) || data.length === 0) {
                    console.log('[autocomplete] No results to display');
                    this.autocompleteDropdown.style.display = 'none';
                    return;
                }


                this.autocompleteDropdown.innerHTML = '';
                // data.forEach(doc => {
                //     const item = document.createElement('div');
                //     item.className = 'autocomplete-dropdown-item';
                //     item.textContent = doc.name;
                //     item.addEventListener('click', (e) => {
                //         e.preventDefault();
                //         this.autocompleteInput.focus();  // ✅ 입력창 포커스 다시 주기
                //         setTimeout(() => {
                //             this.insertDocumentToken(doc.name);  // ✅ 안정적으로 토큰 삽입
                //             this.autocompleteDropdown.style.display = 'none';
                //         }, 0);
                //     });

                //     // item.addEventListener('click', () => {
                //     //     this.insertDocumentToken(doc.name);
                //     //     this.autocompleteDropdown.style.display = 'none';
                //     // });
                //     this.autocompleteDropdown.appendChild(item);
                // });

                data.forEach(doc => {
                    const item = document.createElement('div');
                    item.className = 'autocomplete-dropdown-item';
                    item.textContent = doc.name;

                    // item.addEventListener('click', (e) => {
                    //     e.preventDefault();
                    //     this.autocompleteInput.focus();
                    //     this.insertDocumentToken(doc.name);  // ✅ 즉시 실행
                    //     this.autocompleteDropdown.style.display = 'none';
                    // });

                    item.addEventListener('mousedown', (e) => {
                        // 마우스 누르는 순간 selection 저장
                        const selection = window.getSelection();
                        if (selection && selection.rangeCount > 0) {
                            savedSelection = selection.getRangeAt(0).cloneRange();
                        }
                    });

                    item.addEventListener('mousedown', (e) => {
                        // 클릭 직전 selection 저장
                        const selection = window.getSelection();
                        if (selection && selection.rangeCount > 0) {
                            this.savedRange = selection.getRangeAt(0).cloneRange();
                        }
                    });

                    item.addEventListener('mouseup', (e) => {
                        e.preventDefault();

                        this.autocompleteInput.focus();

                        // 저장된 selection 복원
                        if (this.savedRange) {
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(this.savedRange);
                            this.savedRange = null;
                        }

                        this.insertDocumentToken(doc.name);
                        this.autocompleteDropdown.style.display = 'none';
                    });



                    this.autocompleteDropdown.appendChild(item);
                });



                // 위치 계산
                const inputRect = this.autocompleteInput.getBoundingClientRect();
                const parentRect = this.autocompleteInput.offsetParent.getBoundingClientRect();
                const dropdownHeight = this.autocompleteDropdown.offsetHeight || 200;

                const top = inputRect.top - parentRect.top - dropdownHeight - 4;
                const left = inputRect.left - parentRect.left;

                this.autocompleteDropdown.style.top = `${top}px`;
                this.autocompleteDropdown.style.left = `${left}px`;
                this.autocompleteDropdown.style.display = 'block';

            });
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

        // document.addEventListener('keydown', (e) => {
        //     if (e.key === 'Escape') this.closeDeleteModal();
        // });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeDeleteModal();

            // ✅ Enter 키로 채팅 전송
            if (e.key === 'Enter' && !e.shiftKey) {
                const isInputFocused = document.activeElement === document.getElementById('chatbot-input');
                if (isInputFocused) {
                    e.preventDefault();
                    document.getElementById('chatbot-form').requestSubmit();
                }
            }
        });
    }

    async handleMessageSubmit(e) {
        e.preventDefault();
        if (this.isSubmitting) return;

        const input = document.getElementById('chatbot-input');

        console.log('📌 raw innerHTML:', input.innerHTML);
        console.log('📌 raw innerText:', input.innerText);
        // const tokens = Array.from(input.querySelectorAll('.token')).map(el => el.textContent.trim());
        const tokens = Array.from(input.querySelectorAll('.token')).map(el => {
            const textSpan = el.querySelector('span');
            return textSpan ? textSpan.textContent.trim() : null;
        }).filter(Boolean);
        console.log('📌 추출된 tokens:', tokens);

        const question = Array.from(input.childNodes)
            .filter(n => n.nodeType === Node.TEXT_NODE || (n.nodeType === Node.ELEMENT_NODE && !n.classList.contains('token')))
            .map(n => n.textContent)
            .join(' ')
            .trim();

        // const question = Array.from(input.childNodes)
        //     .filter(n => n.nodeType === Node.TEXT_NODE)
        //     .map(n => n.textContent)
        //     .join(' ')
        //     .trim();
        console.log('📌 전송할 question:', question);

        if (!question && tokens.length === 0) return;
        // this.addMessageToChat('user', question);
        // const inputClone = input.cloneNode(true);
        // this.addMessageToChat('user', inputClone);
        const inputClone = input.cloneNode(true);
        const htmlMessage = this.reconstructUserMessageWithTokens(inputClone);

        this.addMessageToChat('user', htmlMessage);             // 사용자 메시지 화면 출력
        this.updateSessionMessagesInDOM('user', htmlMessage);  // 사용자 메시지 HTML 형태로 세션에 저장




        const sendBtn = document.querySelector('.chatbot-send-btn');
        const btnText = sendBtn?.querySelector('.btn-text');
        const btnLoading = sendBtn?.querySelector('.btn-loading');

        // console.log('📤 메시지 제출됨:', message);
        console.log('📤 메시지 제출됨:', question);


        this.isSubmitting = true;

        // ✅ 전송 버튼 로딩 표시
        if (btnText && btnLoading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline-flex';
            sendBtn.disabled = true;
            // input.disabled = true;
            input.setAttribute('contenteditable', 'false');

        }

        // input.value = '';
        input.innerHTML = '';

        // this.addMessageToChat('user', message);
        this.showLoadingAnimation();

        const sessionId = this.selectedSessionInput ? this.selectedSessionInput.value : null;

        try {
            console.log('📤 최종 fetch 전송 payload:', {
                question,
                doc_filter: tokens,
                session_id: sessionId ? parseInt(sessionId) : null,
                user_id: parseInt(user_id),
                department_id: parseInt(department_id)
            });

            // const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/rag`, {
            // const response = await fetch(`${window.api_base_url}/chat/rag`, {
            const response = await fetch(`${window.api_base_url}/chat/rag`, {


                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    // question: question,
                    question: htmlMessage,  // ✅ 토큰 포함된 HTML 메시지 저장
                    doc_filter: tokens,
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
                showError('오류: ' + (data.error || data.detail || '알 수 없는 오류'));
            }
        } catch (err) {
            console.error('에러 발생:', err);
            showError('메시지 전송 중 오류가 발생했습니다.');
        }

        // ✅ 전송 버튼 상태 복원
        if (btnText && btnLoading) {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            sendBtn.disabled = false;
            // input.disabled = false;
            input.setAttribute('contenteditable', 'true');

            input.focus();
        }

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
            // const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/messages/${sessionId}`);
            // const res = await fetch(`${window.api_base_url}/chat/messages/${sessionId}`);
            const res = await fetch(`${window.api_base_url}/chat/messages/${sessionId}`);


            const data = await res.json();

            if (!data.success) {
                showError("메시지를 불러오는 데 실패했습니다.");
                return;
            }

            this.renderMessages(data.messages);
        } catch (err) {
            console.error("메시지 불러오기 실패:", err);
            showError("메시지 로딩 중 오류 발생");
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
        // const messageRow = document.createElement('div');
        // messageRow.className = `chatbot-msg-row ${type === 'user' ? 'user' : 'bot'}`;
        const messageRow = document.createElement('div');
        messageRow.className = `chatbot-msg-row ${type === 'user' ? 'user' : 'bot'}`;
        if (type === 'user') {
            messageRow.style.justifyContent = 'flex-end';
            messageRow.style.display = 'flex';
        }


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
            // messageContent.textContent = text;
            messageContent.innerHTML = this.reconstructUserMessageWithTokens(text);
        }

        // messageRow.appendChild(messageContent);
        // this.chatArea.appendChild(messageRow);
        if (type === 'user') {
            const wrapper = document.createElement('div');
            // wrapper.style.display = 'inline-flex';                  // 🔥 핵심 변경
            // wrapper.style.flexDirection = 'column';
            // wrapper.style.alignItems = 'flex-end';
            // wrapper.style.maxWidth = '80%';                         // 🔥 말풍선 폭 제한
            // wrapper.style.marginLeft = 'auto';                      // 🔥 오른쪽 정렬 핵심
            wrapper.style.display = 'flex';                  // inline-flex → flex
            wrapper.style.flexDirection = 'column';
            wrapper.style.alignItems = 'flex-end';
            wrapper.style.maxWidth = '100%';                 // 🔥 최대폭을 전체 너비로 (부모가 우측 정렬)
            wrapper.style.marginLeft = 'auto';               // 오른쪽 정렬 유지


            const pureMessageText = (() => {
                if (typeof text === 'string') {
                    const container = document.createElement('div');
                    container.innerHTML = text;
                    container.querySelectorAll('.token').forEach(el => el.remove());
                    return container.textContent.trim();
                } else {
                    return '';
                }
            })();

            const messageBox = document.createElement('div');
            messageBox.className = 'chatbot-msg-user';
            messageBox.textContent = pureMessageText;

            messageBox.style.maxWidth = '480px';
            messageBox.style.wordBreak = 'break-word';
            messageBox.style.display = 'inline-block';

            wrapper.appendChild(messageBox);

            const tokenText = this.extractTokenListFromHTML(text);
            if (tokenText.length > 0) {
                // const tokenDiv = document.createElement('div');
                // tokenDiv.className = 'token-list-below';
                // tokenDiv.textContent = `[${tokenText.join(', ')}]`;
                // tokenDiv.style.fontSize = '12px';
                // tokenDiv.style.color = '#888';
                // tokenDiv.style.marginTop = '4px';
                // tokenDiv.style.marginRight = '4px';
                // wrapper.appendChild(tokenDiv);
                const tokenDiv = document.createElement('div');
                tokenDiv.className = 'token-list-below';
                tokenDiv.style.display = 'flex';
                tokenDiv.style.flexWrap = 'wrap';
                tokenDiv.style.gap = '6px';
                tokenDiv.style.marginTop = '6px';
                tokenDiv.style.justifyContent = 'flex-end';  // 오른쪽 정렬
                tokenText.forEach(token => {
                    const badge = document.createElement('span');
                    badge.textContent = token;
                    badge.style.background = '#f0f0f0';
                    badge.style.color = '#333';
                    badge.style.fontSize = '12px';
                    badge.style.padding = '4px 10px';
                    badge.style.borderRadius = '12px';
                    badge.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
                    badge.style.whiteSpace = 'nowrap';
                    badge.style.fontWeight = '500';
                    tokenDiv.appendChild(badge);
                });
                wrapper.appendChild(tokenDiv);

            }

            messageRow.appendChild(wrapper);
        }

        else {
            messageRow.appendChild(messageContent);
        }
        this.chatArea.appendChild(messageRow);


        if (!this.userScrolling) {
            this.chatArea.scrollTop = this.chatArea.scrollHeight;
        }
    }


    // reconstructUserMessageWithTokens(clonedNode) {
    //     if (!clonedNode) return '';

    //     const childNodes = Array.from(clonedNode.childNodes);
    //     let html = '';

    //     for (const node of childNodes) {
    //         if (node.classList?.contains('token')) {
    //             html += `<span class="token">${node.innerText}</span> `;
    //         } else {
    //             html += node.textContent;
    //         }
    //     }

    //     return html.trim();
    // }
    reconstructUserMessageWithTokens(input) {
        // ✅ 문자열인 경우(세션 불러오기 시)
        // if (typeof input === 'string') {
        //     return input
        //         .replace(/</g, "&lt;")
        //         .replace(/>/g, "&gt;")
        //         .replace(/\n/g, "<br>");
        // }
        if (typeof input === 'string') {
            return input;  // ✅ 저장된 HTML을 그대로 렌더링
        }


        // ✅ DOM 노드인 경우 (방금 보낸 메시지)
        const childNodes = Array.from(input.childNodes || []);
        let html = '';

        for (const node of childNodes) {
            // if (node.classList?.contains('token')) {
            //     html += `<span class="token">${node.innerText}</span> `;
            // }
            if (node.classList?.contains('token')) {
                const textSpan = node.querySelector('span');
                const fileName = textSpan ? textSpan.textContent.trim() : '';
                html += `<span class="token">${fileName}</span> `;
            }

            else {
                html += node.textContent;
            }
        }

        return html.trim();
    }

    extractTokenListFromHTML(html) {
        if (!html || typeof html !== 'string') return [];
        const container = document.createElement('div');
        container.innerHTML = html;
        const tokens = Array.from(container.querySelectorAll('.token')).map(el => el.textContent.trim());
        return tokens;
    }




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
            // const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/session/delete`, {
            // const response = await fetch(`${window.api_base_url}/chat/session/delete`, {
            const response = await fetch(`${window.api_base_url}/chat/session/delete`, {


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
                showError("삭제 실패: " + (data.error || ""));
            }
        } catch (error) {
            console.error("삭제 오류:", error);
            showError("삭제 중 오류 발생");
        }
    }



    getCsrfToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

async function createNewSession() {
    try {
        // const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/chat/session/create`, {
        // const res = await fetch(`${window.api_base_url}/chat/session/create`, {
        const res = await fetch(`${window.api_base_url}/chat/session/create`, {


            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ user_id: user_id })
        });

        const data = await res.json();
        if (!data.success) {
            showError("세션 생성 실패: " + (data.error || ""));
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
        // const script = div.querySelector('.session-messages');
        // if (script) {
        //     try {
        //         const existing = JSON.parse(script.textContent || '[]');
        //         existing.push({
        //             type: 'bot',
        //             text: welcomeText,
        //             time: new Date().toISOString().split('T')[0]
        //         });
        //         script.textContent = JSON.stringify(existing);
        //     } catch (e) {
        //         console.error('세션 메시지 초기화 실패:', e);
        //     }
        // }
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

        // ✅ 세션 리스트 다시 바인딩 (세션 추가 후 세션 전환 안 되는 버그 해결)
        if (window.chatBot) {
            window.chatBot.refreshSessionList();
        }


    } catch (e) {
        console.error("세션 생성 실패:", e);
        showError("세션 생성 중 오류가 발생했습니다.");
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

// document.addEventListener('DOMContentLoaded', function () {
//     if (!window.chatBot) {
//         window.chatBot = new ChatBot();  // ✅ 한 번만 실행되도록 보장
//     }
// });

// document.addEventListener('DOMContentLoaded', function () {
//     if (!window.chatBot) {
//         window.chatBot = new ChatBot();
//     }

//     // 기존 서버 렌더링된 세션 아이템들에 클릭 이벤트 바인딩
//     const items = document.querySelectorAll('.chatbot-session-item');
//     items.forEach((item) => {
//         item.addEventListener('click', (e) => {
//             if (e.target.closest('.delete-session-btn')) return;
//             window.chatBot.selectSession(item);  // ✅ 세션 선택
//         });

//         const deleteBtn = item.querySelector('.delete-session-btn');
//         if (deleteBtn) {
//             deleteBtn.addEventListener('click', (e) => {
//                 e.stopPropagation();
//                 window.chatBot.openDeleteModal(deleteBtn.getAttribute('data-session-id'));
//             });
//         }
//     });
// });
document.addEventListener('DOMContentLoaded', function () {
    if (!window.chatBot) {
        window.chatBot = new ChatBot();
        window.chatBot.refreshSessionList();  // ✅ 필수: DOM 렌더링된 세션 리스트로 이벤트 바인딩
    }
});



