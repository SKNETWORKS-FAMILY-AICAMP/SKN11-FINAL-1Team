// mentee_task_list.js
// 하위 테스크 토글 함수 (전역)
function toggleSubtaskList(toggleBtn) {
  var subtaskList = toggleBtn.closest('.task-card').querySelector('.subtask-list');
  if (subtaskList) {
    subtaskList.classList.toggle('open');
    if (subtaskList.classList.contains('open')) {
      toggleBtn.textContent = '▲ 하위 접기';
    } else {
      toggleBtn.textContent = '▼ 하위 ' + subtaskList.children.length + '개';
    }
  }
}

document.addEventListener('DOMContentLoaded', function() {
  // 하위 테스크(서브태스크) 클릭 시 상세 정보 표시
  function attachSubtaskClickEvents() {
    document.querySelectorAll('.subtask-item').forEach(function(item) {
      item.addEventListener('click', function(e) {
        e.stopPropagation(); // 상위 카드 클릭 방지
        const taskId = this.getAttribute('data-task-id');
        if (!taskId) return;
        fetch(`/mentee/task_detail/${taskId}/`).then(resp => resp.json()).then(data => {
          if (data.success && data.task) {
            updateDetailFromData(data.task);
            // 좌측 카드 선택 해제, 해당 subtask 강조(선택 효과)
            document.querySelectorAll('.task-card').forEach(c => c.classList.remove('selected'));
            document.querySelectorAll('.subtask-item').forEach(s => s.classList.remove('selected'));
            this.classList.add('selected');
          }
        });
      });
    });
  }
  attachSubtaskClickEvents();

  // 동적으로 생성되는 경우를 위해 토글 후에도 이벤트 재부착
  document.querySelectorAll('.subtask-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() {
      setTimeout(attachSubtaskClickEvents, 0);
    });
  });
  // 하위 테스크 토글 버튼 이벤트
  document.querySelectorAll('.subtask-toggle').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const subtaskList = this.nextElementSibling;
      if (!subtaskList) return;
      if (subtaskList.style.display === 'none' || subtaskList.style.display === '') {
        subtaskList.style.display = 'block';
        this.textContent = '▲ 하위 접기';
      } else {
        subtaskList.style.display = 'none';
        // 하위 개수 표시
        const count = subtaskList.querySelectorAll('.subtask-item').length;
        this.textContent = '▼ 하위 ' + count + '개';
      }
    });
  });
  // 하위 테스크 생성 모달 관련
  const subtaskModal = document.getElementById('subtask-modal');
  const subtaskBtn = document.getElementById('task-detail-subtask-btn');
  const subtaskForm = document.getElementById('subtask-form');
  const subtaskCancelBtn = document.getElementById('subtask-cancel-btn');
  subtaskBtn.addEventListener('click', function() {
    if (!currentTask) return alert('상위 Task를 먼저 선택하세요.');
    subtaskModal.style.display = 'flex';
    subtaskForm.reset();
    document.getElementById('subtask-parent-title').value = currentTask.title || '';
    document.getElementById('subtask-parent-id').value = currentTask.id;
    document.getElementById('subtask-priority').value = '';
    document.getElementById('subtask-status').value = '진행 전';
    document.getElementById('subtask-end-date').value = '';
  });
  // 닫기 버튼(×)과 취소 버튼 모두 모달 닫기
  const subtaskCloseBtn = document.getElementById('subtask-close-btn');
  function closeSubtaskModal() {
    subtaskModal.style.display = 'none';
  }
  subtaskCancelBtn.addEventListener('click', closeSubtaskModal);
  if (subtaskCloseBtn) {
    subtaskCloseBtn.addEventListener('click', closeSubtaskModal);
  }
  // ESC 키로 모달 닫기
  document.addEventListener('keydown', function(e) {
    if (subtaskModal.style.display === 'flex' && (e.key === 'Escape' || e.key === 'Esc')) {
      closeSubtaskModal();
    }
  });
  subtaskForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!currentTask) return alert('상위 Task를 먼저 선택하세요.');
    const title = document.getElementById('subtask-title').value.trim();
    const guideline = document.getElementById('subtask-guideline').value.trim();
    const description = document.getElementById('subtask-desc').value.trim();
    const status = document.getElementById('subtask-status').value;
    const priority = document.getElementById('subtask-priority').value;
    const end_date = document.getElementById('subtask-end-date').value;
    const parent_id = document.getElementById('subtask-parent-id').value;
    // 상위 Task의 mentorship_id, week, order도 전달
    const mentorship_id = currentTask.mentorship_id || (currentTask.mentorship_id_id || null);
    const week = currentTask.week;
    const order = null;
    if (!title) return alert('제목을 입력하세요.');
    try {
      const resp = await fetch(`/mentee/create_subtask/${parent_id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': (document.querySelector('input[name=csrfmiddlewaretoken]')||{}).value || ''
        },
        body: JSON.stringify({title, guideline, description, status, priority, end_date, mentorship_id, week, order})
      });
      const data = await resp.json();
      if (data.success) {
        alert('하위 테스크가 생성되었습니다.');
        subtaskModal.style.display = 'none';
        // 좌측 카드의 서브태스크 리스트에 바로 추가
        const card = document.querySelector(`.task-card[data-task-id="${parent_id}"]`);
        if (card) {
          let subtaskList = card.querySelector('.subtask-list');
          if (!subtaskList) {
            // 없으면 생성
            subtaskList = document.createElement('div');
            subtaskList.className = 'subtask-list';
            subtaskList.style.display = 'block';
            card.appendChild(subtaskList);
          } else {
            subtaskList.style.display = 'block';
          }
          // 버튼이 없으면 생성
          let toggleBtn = card.querySelector('.subtask-toggle');
          if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'subtask-toggle';
            toggleBtn.style = 'margin:6px 0 0 0; font-size:13px; background:none; border:none; color:#1976d2; cursor:pointer;';
            card.insertBefore(toggleBtn, subtaskList);
            toggleBtn.addEventListener('click', function() {
              if (subtaskList.style.display === 'none' || subtaskList.style.display === '') {
                subtaskList.style.display = 'block';
                toggleBtn.textContent = '▲ 하위 접기';
              } else {
                subtaskList.style.display = 'none';
                const count = subtaskList.querySelectorAll('.subtask-item').length;
                toggleBtn.textContent = '▼ 하위 ' + count + '개';
              }
            });
          }
          // 새 subtask DOM 추가
          const subDiv = document.createElement('div');
          subDiv.className = 'subtask-item';
          subDiv.setAttribute('data-task-id', data.subtask_id);
          subDiv.style = 'padding:4px 0 4px 12px; border-left:2px solid #e0e0e0; margin-bottom:2px; font-size:14px; color:#444; cursor:pointer;';
          subDiv.innerHTML = `<span class="subtask-title">${title}</span> <span class="subtask-status" style="margin-left:8px; font-size:12px; color:#888;">[${status}]</span>`;
          subDiv.addEventListener('click', function(e) {
            e.stopPropagation();
            fetch(`/mentee/task_detail/${data.subtask_id}/`).then(resp => resp.json()).then(dt => {
              if (dt.success && dt.task) {
                updateDetailFromData(dt.task);
                document.querySelectorAll('.task-card').forEach(c => c.classList.remove('selected'));
                document.querySelectorAll('.subtask-item').forEach(s => s.classList.remove('selected'));
                subDiv.classList.add('selected');
              }
            });
          });
          subtaskList.appendChild(subDiv);
          // 토글 버튼 텍스트 갱신
          const count = subtaskList.querySelectorAll('.subtask-item').length;
          toggleBtn.textContent = '▼ 하위 ' + count + '개';
        }
        // 필요시 상세정보 갱신
        if (currentTask && currentTask.id) fetchAndUpdateDetail(currentTask.id);
      } else {
        alert('생성 실패: ' + (data.error || '오류'));
      }
    } catch (err) {
      alert('생성 중 오류: ' + err);
    }
  });
  const cards = document.querySelectorAll('.task-card');
  let currentTask = null; // 현재 선택된 task 정보 저장
  function updateDetailFromData(task) {
    currentTask = task;
    // 상태 뱃지 색상
    let statusClass = '';
    if (task.status === '진행 전') statusClass = 'not-started';
    else if (task.status === '진행 중') statusClass = 'in-progress';
    else if (task.status === '검토 요청') statusClass = 'review-requested';
    else if (task.status === '완료' || task.status === '완료됨') statusClass = 'done';
    // 우측 영역 갱신 (기존 코드 ...)
    const titleEl = document.getElementById('detail-title');
    titleEl.innerHTML = `<span class="status-badge ${statusClass}">${task.status}</span> <span class="${statusClass === 'done' ? 'done' : ''}">${task.title}</span>`;
    const xpEl = document.getElementById('detail-xp');
    if (xpEl) xpEl.innerHTML = '';
    // guideline이 null/빈값이면 표시하지 않음
    const descEl = document.getElementById('detail-desc');
    if (task.guideline && String(task.guideline).trim() !== '') {
      descEl.textContent = task.guideline;
      descEl.style.display = '';
    } else {  
      descEl.textContent = '';
      descEl.style.display = 'none';
    }
    // 난이도/디데이 메타
    const metaRow = document.querySelector('.task-detail-meta-row');
    let badgeClass = 'yellow';
    if (task.priority === '상') badgeClass = 'red';
    else if (task.priority === '중') badgeClass = 'green';
    metaRow.innerHTML = `<span class="task-badge ${badgeClass}" id="detail-badge">${task.priority || '하'}</span> <span class="d-day-badge">${task.end_date || ''}</span>`;
    // description을 리스트로 표시
    const listDiv = document.getElementById('detail-list');
    listDiv.innerHTML = '';
    if (task.description) {
      const items = String(task.description).split('\n').filter(x => x.trim() !== '');
      const ul = document.createElement('ul');
      items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
      });
      listDiv.appendChild(ul);
    } else if (task.desc) {
      const ul = document.createElement('ul');
      const li = document.createElement('li');
      li.textContent = task.desc;
      ul.appendChild(li);
      listDiv.appendChild(ul);
    }
    // 댓글 목록 표시
    const chatMsgDiv = document.getElementById('chat-messages');
    if (chatMsgDiv) {
      chatMsgDiv.innerHTML = '';
      if (task.memos && Array.isArray(task.memos) && task.memos.length > 0) {
        task.memos.forEach(memo => {
          const msgDiv = document.createElement('div');
          msgDiv.className = 'chat-message';
          msgDiv.innerHTML = `
            <span class="chat-user">${memo.user}</span>
            <span class="chat-text">${memo.comment}</span>
            <span class="chat-time">${memo.create_date}</span>
          `;
          chatMsgDiv.appendChild(msgDiv);
        });
      } else {
        chatMsgDiv.innerHTML = '<div style="color:#888; font-size:15px;">댓글이 없습니다.</div>';
      }
    }
    // 입력창 초기화
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.value = '';
  }
  // 댓글 작성
  const chatSendBtn = document.getElementById('chat-send-btn');
  const chatInput = document.getElementById('chat-input');
  if (chatSendBtn && chatInput) {
    chatSendBtn.addEventListener('click', async function() {
      if (!currentTask || !chatInput.value.trim()) return;
      const comment = chatInput.value.trim();
      try {
        const resp = await fetch(`/mentee/task_comment/${currentTask.id}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': (document.querySelector('input[name=csrfmiddlewaretoken]')||{}).value || ''
          },
          body: JSON.stringify({comment})
        });
        const data = await resp.json();
        if (data.success && data.memo) {
          if (!currentTask.memos) currentTask.memos = [];
          currentTask.memos.push(data.memo);
          updateDetailFromData(currentTask);
        } else {
          alert('댓글 등록 실패: ' + (data.error || '오류'));
        }
      } catch (err) {
        alert('댓글 등록 중 오류: ' + err);
      }
    });
    chatInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        chatSendBtn.click();
      }
    });
  }

  // 좌측 Task 카드 클릭 시 상세/댓글 동적 갱신
  cards.forEach(card => {
    card.addEventListener('click', async function() {
      const taskId = this.dataset.taskId || this.getAttribute('data-task-id');
      if (!taskId) return;
      try {
        const resp = await fetch(`/mentee/task_detail/${taskId}/`);
        const data = await resp.json();
        if (data.success && data.task) {
          updateDetailFromData(data.task);
        }
      } catch (e) {
        alert('상세정보 불러오기 실패');
      }
    });
  });

  // 최초 로딩 시 첫 번째 Task 선택
  if (cards.length > 0) {
    const firstCard = cards[0];
    const taskId = firstCard.dataset.taskId || firstCard.getAttribute('data-task-id');
    if (taskId) {
      fetch(`/mentee/task_detail/${taskId}/`).then(resp => resp.json()).then(data => {
        if (data.success && data.task) updateDetailFromData(data.task);
      });
    }
  }
  // 편집 폼 토글 및 저장/취소
  const editBtn = document.getElementById('task-edit-btn');
  const editForm = document.getElementById('task-edit-form');
  const descDiv = document.getElementById('detail-desc');
  const listDiv = document.getElementById('detail-list');
  const editStatus = document.getElementById('edit-status');
  const editTitle = document.getElementById('edit-title');
  const editGuideline = document.getElementById('edit-guideline');
  const editDescription = document.getElementById('edit-description');
  const editPriority = document.getElementById('edit-priority');
  const editEndDate = document.getElementById('edit-end-date');
  const saveBtn = document.getElementById('edit-save-btn');
  const cancelBtn = document.getElementById('edit-cancel-btn');
  let isEditing = false;

  function showEditForm() {
    if (!currentTask) return;
    // 기존 영역 숨김
    document.getElementById('detail-header-row').style.display = 'none';
    document.getElementById('detail-meta-row').style.display = 'none';
    // 기존 값 세팅
    editStatus.value = currentTask.status || '진행 전';
    editTitle.value = currentTask.title || '';
    editGuideline.value = currentTask.guideline || '';
    editDescription.value = currentTask.description || '';
    editPriority.value = currentTask.priority || '하';
    if (currentTask.end_date) {
      editEndDate.value = String(currentTask.end_date).slice(0, 10);
    } else {
      editEndDate.value = '';
    }
    // 기존 폼 로직
    editForm.style.display = '';
    descDiv.style.display = 'none';
    listDiv.style.display = 'none';
    isEditing = true;
  }
  function hideEditForm() {
    editForm.style.display = 'none';
    // 숨겼던 영역 다시 표시
    document.getElementById('detail-header-row').style.display = '';
    document.getElementById('detail-meta-row').style.display = '';
    descDiv.style.display = '';
    listDiv.style.display = '';
    isEditing = false;
  }
  if (editBtn) {
    editBtn.addEventListener('click', function() {
      if (isEditing) return;
      showEditForm();
    });
  }
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function(e) {
      e.preventDefault();
      hideEditForm();
    });
  }
  if (editForm) {
    editForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      // DB 저장 AJAX
      const payload = {
        status: editStatus.value,
        title: editTitle.value,
        guideline: editGuideline.value,
        description: editDescription.value,
        priority: editPriority.value,
        end_date: editEndDate.value
      };
      try {
        const resp = await fetch(`/mentee/task_update/${currentTask.id}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': (document.querySelector('input[name=csrfmiddlewaretoken]')||{}).value || ''
          },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (data.success) {
          // 프론트 상태도 반영
          currentTask.status = payload.status;
          currentTask.title = payload.title;
          currentTask.guideline = payload.guideline;
          currentTask.description = payload.description;
          currentTask.priority = payload.priority;
          currentTask.end_date = payload.end_date;
          // 좌측 카드도 동기화
          const card = document.querySelector(`.task-card[data-task-id="${currentTask.id}"]`);
          if (card) {
            // 상태 뱃지
            const statusBadge = card.querySelector('.status-badge');
            if (statusBadge) {
              statusBadge.textContent = payload.status;
              statusBadge.className = 'status-badge';
              if (payload.status === '진행 전') statusBadge.classList.add('not-started');
              else if (payload.status === '진행 중') statusBadge.classList.add('in-progress');
              else if (payload.status === '검토 요청') statusBadge.classList.add('review-requested');
              else if (payload.status === '완료' || payload.status === '완료됨') statusBadge.classList.add('done');
            }
            // 제목
            const titleSpan = card.querySelector('.task-title');
            if (titleSpan) {
              titleSpan.textContent = payload.title;
              if (payload.status === '완료' || payload.status === '완료됨') titleSpan.classList.add('done');
              else titleSpan.classList.remove('done');
            }
            // 우선순위 뱃지
            const badge = card.querySelector('.task-badge');
            if (badge) {
              badge.textContent = payload.priority || '하';
              badge.className = 'task-badge';
              if (payload.priority === '상') badge.classList.add('red');
              else if (payload.priority === '중') badge.classList.add('green');
              else badge.classList.add('yellow');
            }
            // 마감일
            const dday = card.querySelector('.d-day-badge');
            if (dday) dday.textContent = payload.end_date || '';
            // 설명
            const descDiv = card.querySelector('.task-desc');
            if (descDiv) descDiv.textContent = payload.description || '';
            // 카드 전체 클래스(상태별)
            card.classList.remove('not-started','in-progress','review-requested','done');
            if (payload.status === '진행 전') card.classList.add('not-started');
            else if (payload.status === '진행 중') card.classList.add('in-progress');
            else if (payload.status === '검토 요청') card.classList.add('review-requested');
            else if (payload.status === '완료' || payload.status === '완료됨') card.classList.add('done');
          }
          updateDetailFromData(currentTask);
          hideEditForm();
        } else {
          alert('저장 실패: ' + (data.error || '오류'));
        }
      } catch (err) {
        alert('저장 중 오류 발생: ' + err);
      }
    });
  }
  async function fetchAndUpdateDetail(taskId) {
    try {
      const resp = await fetch(`/mentee/task_detail/${taskId}/`);
      if (!resp.ok) throw new Error('상세 정보를 불러올 수 없습니다');
      const data = await resp.json();
      if (data.success && data.task) {
        updateDetailFromData(data.task);
      }
    } catch (e) {
      alert('상세 정보를 불러오지 못했습니다.');
    }
  }
  cards.forEach(card => {
    card.addEventListener('click', function() {
      if (isEditing) return; // 편집 중이면 카드 선택 비활성화
      cards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const taskId = card.getAttribute('data-task-id');
      if (taskId) fetchAndUpdateDetail(taskId);
    });
  });
  // 최초 로딩 시 첫 번째 Task 선택
  if (cards.length > 0) {
    const firstTaskId = cards[0].getAttribute('data-task-id');
    if (firstTaskId) fetchAndUpdateDetail(firstTaskId);
  }
});
