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
  // 정렬/필터 관련 변수
  const taskSort = document.getElementById('task-sort');
  const taskFilterStatus = document.getElementById('task-filter-status');
  const taskFilterPriority = document.getElementById('task-filter-priority');
  
  // 원본 태스크 데이터 저장 (초기화 시 한 번 수집)
  let originalTaskData = [];
  
  // 초기 태스크 데이터 수집
  function collectOriginalTaskData() {
    originalTaskData = [];
    const tasklist = document.getElementById('tasklist-left');
    const weekHeaders = tasklist.querySelectorAll('div[style*="font-weight:bold"]');
    
    weekHeaders.forEach(header => {
      const weekMatch = header.textContent.match(/(\d+)주차/);
      const week = weekMatch ? parseInt(weekMatch[1]) : 0;
      
      let nextElement = header.nextElementSibling;
      while (nextElement && !nextElement.textContent.includes('주차')) {
        if (nextElement.classList && nextElement.classList.contains('task-card')) {
          const taskData = {
            element: nextElement.cloneNode(true), // 원본 보존
            week: week,
            title: nextElement.getAttribute('data-title') || nextElement.querySelector('.task-title')?.textContent || '',
            status: nextElement.getAttribute('data-status') || '',
            priority: nextElement.getAttribute('data-priority') || '하',
            endDate: nextElement.getAttribute('data-scheduled_end_date') || nextElement.getAttribute('data-scheduled-end-date') || '',
            id: nextElement.getAttribute('data-task-id') || '',
            dday: nextElement.getAttribute('data-dday') || ''
          };
          originalTaskData.push(taskData);
        }
        nextElement = nextElement.nextElementSibling;
      }
    });
    
    console.log('Collected task data:', originalTaskData);
  }
  
  // 마감일까지 남은 일수 계산
  function getDaysUntilDeadline(endDate) {
    if (!endDate) return 999999; // 마감일이 없으면 가장 뒤로
    const today = new Date();
    const deadline = new Date(endDate);
    const diffTime = deadline - today;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
  
  // 태스크 정렬 함수
  function sortTasks(tasks, sortBy) {
    return tasks.sort((a, b) => {
      switch(sortBy) {
        case 'deadline':
          const daysA = getDaysUntilDeadline(a.endDate);
          const daysB = getDaysUntilDeadline(b.endDate);
          if (daysA !== daysB) return daysA - daysB; // 마감일이 가까운 것이 먼저
          return a.title.localeCompare(b.title);
          
        case 'week':
        default:
          if (a.week !== b.week) return a.week - b.week;
          return a.title.localeCompare(b.title);
      }
    });
  }
  
  // 태스크 필터 함수
  function filterTasks(tasks, statusFilter, priorityFilter) {
    return tasks.filter(task => {
      const statusMatch = statusFilter === 'all' || task.status === statusFilter;
      const priorityMatch = priorityFilter === 'all' || task.priority === priorityFilter;
      return statusMatch && priorityMatch;
    });
  }
  
  // 태스크 목록 렌더링
  function renderTasks() {
    const sortBy = taskSort.value;
    const statusFilter = taskFilterStatus.value;
    const priorityFilter = taskFilterPriority.value;
    
    console.log('Rendering with:', { sortBy, statusFilter, priorityFilter });
    
    const tasklist = document.getElementById('tasklist-left');
    
    // 기존 태스크들 제거 (컨트롤과 제목은 유지)
    const controls = tasklist.querySelector('.task-controls');
    const title = tasklist.querySelector('.tasklist-title');
    
    // 모든 자식 요소 제거
    while (tasklist.firstChild) {
      tasklist.removeChild(tasklist.firstChild);
    }
    
    // 제목과 컨트롤 다시 추가
    tasklist.appendChild(title);
    tasklist.appendChild(controls);
    
    // 원본 데이터로부터 작업
    let workingTasks = originalTaskData.map(task => ({
      ...task,
      element: task.element.cloneNode(true) // 깊은 복사
    }));
    
    // 필터링
    const filteredTasks = filterTasks(workingTasks, statusFilter, priorityFilter);
    console.log('Filtered tasks:', filteredTasks.length);
    
    if (filteredTasks.length === 0) {
      const noResult = document.createElement('div');
      noResult.style.cssText = 'padding: 20px; text-align: center; color: #888; font-size: 14px;';
      noResult.textContent = '조건에 맞는 태스크가 없습니다.';
      tasklist.appendChild(noResult);
      return;
    }
    
    if (sortBy === 'week') {
      // 주차별 정렬은 기존 구조 유지
      const weekGroups = {};
      
      filteredTasks.forEach(task => {
        if (!weekGroups[task.week]) {
          weekGroups[task.week] = [];
        }
        weekGroups[task.week].push(task);
      });
      
      // 주차 순서대로 표시
      Object.keys(weekGroups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(week => {
        // 주차 헤더 추가
        const weekHeader = document.createElement('div');
        weekHeader.style.cssText = 'font-weight:bold; margin:18px 0 8px 0; color:#1976d2;';
        weekHeader.textContent = `${week}주차`;
        tasklist.appendChild(weekHeader);
        
        // 해당 주차의 태스크들 추가
        const sortedTasks = sortTasks(weekGroups[week], 'week');
        sortedTasks.forEach(task => {
          tasklist.appendChild(task.element);
        });
      });
    } else {
      // 마감일별 정렬은 모든 태스크를 하나로 합쳐서 정렬
      const sortedTasks = sortTasks(filteredTasks, sortBy);
      
      // 정렬된 태스크들을 순서대로 추가
      sortedTasks.forEach(task => {
        tasklist.appendChild(task.element);
      });
    }
    
    // 이벤트 재연결
    attachTaskCardEvents();
    attachSubtaskClickEvents();
    
    // 첫 번째 태스크 자동 선택
    const firstCard = tasklist.querySelector('.task-card');
    if (firstCard) {
      firstCard.classList.add('selected');
      const taskId = firstCard.getAttribute('data-task-id');
      if (taskId) {
        fetch(`/mentee/task_detail/${taskId}/`).then(resp => resp.json()).then(data => {
          if (data.success && data.task) updateDetailFromData(data.task, false);
        });
      }
    }
  }
  
  // 태스크 카드 이벤트 재연결
  function attachTaskCardEvents() {
    const cards = document.querySelectorAll('.task-card');
    cards.forEach(card => {
      // 기존 이벤트 리스너 제거를 위해 클론 후 교체
      const newCard = card.cloneNode(true);
      card.parentNode.replaceChild(newCard, card);
      
      newCard.addEventListener('click', async function() {
        // 편집 중일 때는 클릭 차단
        if (isEditing) {
          alert('편집을 완료하거나 취소한 후 다른 태스크를 선택할 수 있습니다.');
          return;
        }
        
        const taskId = this.dataset.taskId || this.getAttribute('data-task-id');
        if (!taskId) return;
        
        // 선택 상태 업데이트
        document.querySelectorAll('.task-card').forEach(c => c.classList.remove('selected'));
        document.querySelectorAll('.subtask-item').forEach(s => s.classList.remove('selected'));
        this.classList.add('selected');
        
        try {
          const resp = await fetch(`/mentee/task_detail/${taskId}/`);
          const data = await resp.json();
          if (data.success && data.task) {
            updateDetailFromData(data.task, false); // 상위 태스크이므로 false
          }
        } catch (e) {
          alert('상세정보 불러오기 실패');
        }
      });
    });
    
    // 하위 태스크 토글 버튼 이벤트 재연결
    document.querySelectorAll('.subtask-toggle').forEach(function(btn) {
      // 기존 이벤트 리스너 제거를 위해 클론 후 교체
      const newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);
      
      newBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // 카드 클릭 방지
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
        // 하위 태스크 이벤트 재연결
        setTimeout(attachSubtaskClickEvents, 0);
      });
    });
  }
  
  // 정렬/필터 이벤트 리스너
  if (taskSort) {
    taskSort.addEventListener('change', renderTasks);
  }
  if (taskFilterStatus) {
    taskFilterStatus.addEventListener('change', renderTasks);
  }
  if (taskFilterPriority) {
    taskFilterPriority.addEventListener('change', renderTasks);
  }
  
  // 페이지 로드 시 원본 데이터 수집
  collectOriginalTaskData();

  // 하위 테스크(서브태스크) 클릭 시 상세 정보 표시
  function attachSubtaskClickEvents() {
    document.querySelectorAll('.subtask-item').forEach(function(item) {
      // 기존 이벤트 리스너 제거를 위해 클론 후 교체
      const newItem = item.cloneNode(true);
      item.parentNode.replaceChild(newItem, item);
      
      newItem.addEventListener('click', function(e) {
        e.stopPropagation(); // 상위 카드 클릭 방지
        
        // 편집 중일 때는 클릭 차단
        if (isEditing) {
          alert('편집을 완료하거나 취소한 후 다른 태스크를 선택할 수 있습니다.');
          return;
        }
        
        const taskId = this.getAttribute('data-task-id');
        if (!taskId) return;
        fetch(`/mentee/task_detail/${taskId}/`).then(resp => resp.json()).then(data => {
          if (data.success && data.task) {
            updateDetailFromData(data.task, true); // 두 번째 인자로 하위 태스크임을 표시
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
    const mentorship_id = currentTask.mentorship_id || (currentTask.mentorship_id || null);
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
        body: JSON.stringify({title, guideline, description, status, priority, scheduled_end_date: end_date, mentorship_id, week, order})
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
          subDiv.style = 'padding:4px 0 4px 12px; border-left:2px solid #e0e0e0; margin-bottom:2px; font-size:14px; color:#444; cursor:pointer; display: flex; align-items: center; gap: 6px;';
          
          // 상태 배지 클래스 설정
          let statusBadgeClass = '';
          if (status === '진행전') statusBadgeClass = 'not-started';
          else if (status === '진행중') statusBadgeClass = 'in-progress';
          else if (status === '검토요청') statusBadgeClass = 'review-requested';
          else if (status === '완료' || status === '완료됨') statusBadgeClass = 'done';
          
          subDiv.innerHTML = `<span class="status-badge ${statusBadgeClass}" style="font-size: 11px; padding: 1px 8px;">${status}</span><span class="subtask-title" style="flex: 1;">${title}</span>`;
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
        // 원본 데이터 다시 수집 (하위 태스크 추가 반영)
        collectOriginalTaskData();
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
  function updateDetailFromData(task, isSubtask = false) {
    currentTask = task;
    // 상태 뱃지 색상
    let statusClass = '';
    if (task.status === '진행전') statusClass = 'not-started';
    else if (task.status === '진행중') statusClass = 'in-progress';
    else if (task.status === '검토요청') statusClass = 'review-requested';
    else if (task.status === '완료' || task.status === '완료됨') statusClass = 'done';
    
    // 하위 태스크 생성 버튼 표시/숨김 제어
    const subtaskBtn = document.getElementById('task-detail-subtask-btn');
    if (subtaskBtn) {
      if (isSubtask) {
        subtaskBtn.style.display = 'none'; // 하위 태스크인 경우 버튼 숨김
      } else {
        subtaskBtn.style.display = 'inline-block'; // 상위 태스크인 경우 버튼 표시
      }
    }
    
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
    // 난이도/마감일 메타
    const metaRow = document.querySelector('.task-detail-meta-row');
    let badgeClass = 'yellow';
    if (task.priority === '상') badgeClass = 'red';
    else if (task.priority === '중') badgeClass = 'green';
    
    // 마감일 표시 (날짜 형식)
    let deadlineText = task.scheduled_end_date || '';
    
    metaRow.innerHTML = `<span class="task-badge ${badgeClass}" id="detail-badge">${task.priority || '하'}</span> <span class="d-day-badge">${deadlineText}</span>`;
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

  // 좌측 Task 카드 클릭 시 상세/댓글 동적 갱신 (초기 연결)
  attachTaskCardEvents();
  
  // 최초 로딩 시 첫 번째 Task 선택
  if (document.querySelectorAll('.task-card').length > 0) {
    const firstCard = document.querySelectorAll('.task-card')[0];
    const taskId = firstCard.dataset.taskId || firstCard.getAttribute('data-task-id');
    if (taskId) {
      firstCard.classList.add('selected');
      fetch(`/mentee/task_detail/${taskId}/`).then(resp => resp.json()).then(data => {
        if (data.success && data.task) updateDetailFromData(data.task, false); // 상위 태스크이므로 false
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
    if (currentTask.scheduled_end_date) {
      editEndDate.value = String(currentTask.scheduled_end_date).slice(0, 10);
    } else {
      editEndDate.value = '';
    }
    // 기존 폼 로직
    editForm.style.display = '';
    descDiv.style.display = 'none';
    listDiv.style.display = 'none';
    isEditing = true;
    
    // 편집 중일 때 좌측 카드들 비활성화
    const taskListLeft = document.getElementById('tasklist-left');
    if (taskListLeft) {
      taskListLeft.classList.add('editing-mode');
    }
  }
  function hideEditForm() {
    editForm.style.display = 'none';
    // 숨겼던 영역 다시 표시
    document.getElementById('detail-header-row').style.display = '';
    document.getElementById('detail-meta-row').style.display = '';
    descDiv.style.display = '';
    listDiv.style.display = '';
    isEditing = false;
    
    // 편집 완료 시 좌측 카드들 다시 활성화
    const taskListLeft = document.getElementById('tasklist-left');
    if (taskListLeft) {
      taskListLeft.classList.remove('editing-mode');
    }
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
        scheduled_end_date: editEndDate.value
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
          const oldStatus = currentTask.status;
          currentTask.status = payload.status;
          currentTask.title = payload.title;
          currentTask.guideline = payload.guideline;
          currentTask.description = payload.description;
          currentTask.priority = payload.priority;
          currentTask.scheduled_end_date = payload.scheduled_end_date;
          
          // 좌측 카드도 동기화
          const card = document.querySelector(`.task-card[data-task-id="${currentTask.id}"]`);
          if (card) {
            // 상태 뱃지
            const statusBadge = card.querySelector('.status-badge');
            if (statusBadge) {
              statusBadge.textContent = payload.status;
              statusBadge.className = 'status-badge';
              if (payload.status === '진행전') statusBadge.classList.add('not-started');
              else if (payload.status === '진행중') statusBadge.classList.add('in-progress');
              else if (payload.status === '검토요청') statusBadge.classList.add('review-requested');
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
            // D-day 배지 (task-card-header 내의 task-dday)
            const taskDday = card.querySelector('.task-dday');
            if (taskDday && payload.scheduled_end_date) {
              const endDate = new Date(payload.scheduled_end_date);
              const today = new Date();
              const diffTime = endDate - today;
              const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
              
              // D-day 또는 D+ 표시
              if (diffDays >= 0) {
                taskDday.textContent = `D-${diffDays}`;
              } else {
                taskDday.textContent = `D+${Math.abs(diffDays)}`;
              }
              
              // 긴급도에 따른 클래스 적용
              taskDday.classList.remove('urgent', 'warning');
              if (diffDays <= 1) {
                taskDday.classList.add('urgent');
              } else if (diffDays <= 3) {
                taskDday.classList.add('warning');
              }
            }
            // 설명
            const descDiv = card.querySelector('.task-desc');
            if (descDiv) descDiv.textContent = payload.description || '';
            // 카드 전체 클래스(상태별)
            card.classList.remove('not-started','in-progress','review-requested','done');
            if (payload.status === '진행전') card.classList.add('not-started');
            else if (payload.status === '진행중') card.classList.add('in-progress');
            else if (payload.status === '검토요청') card.classList.add('review-requested');
            else if (payload.status === '완료' || payload.status === '완료됨') card.classList.add('done');
          }
          
          // 상위 태스크가 '완료'로 변경된 경우, 모든 하위 태스크 상태도 '완료'로 변경
          if (oldStatus !== '완료' && (payload.status === '완료' || payload.status === '완료됨')) {
            const subtaskItems = card.querySelectorAll('.subtask-item');
            subtaskItems.forEach(subtaskItem => {
              const subtaskStatusBadge = subtaskItem.querySelector('.status-badge');
              if (subtaskStatusBadge) {
                subtaskStatusBadge.textContent = '완료';
                subtaskStatusBadge.className = 'status-badge done';
              }
            });
          }
          
          // 하위 태스크인 경우 좌측 하위 태스크 요소도 업데이트
          const subtaskItem = document.querySelector(`.subtask-item[data-task-id="${currentTask.id}"]`);
          if (subtaskItem) {
            const subtaskStatusBadge = subtaskItem.querySelector('.status-badge');
            if (subtaskStatusBadge) {
              subtaskStatusBadge.textContent = payload.status;
              subtaskStatusBadge.className = 'status-badge';
              if (payload.status === '진행전') subtaskStatusBadge.classList.add('not-started');
              else if (payload.status === '진행중') subtaskStatusBadge.classList.add('in-progress');
              else if (payload.status === '검토요청') subtaskStatusBadge.classList.add('review-requested');
              else if (payload.status === '완료' || payload.status === '완료됨') subtaskStatusBadge.classList.add('done');
            }
            const subtaskTitle = subtaskItem.querySelector('.subtask-title');
            if (subtaskTitle) {
              subtaskTitle.textContent = payload.title;
            }
          }
          updateDetailFromData(currentTask);
          
          // 상위 태스크가 완료된 경우 원본 데이터도 업데이트
          if (oldStatus !== '완료' && (payload.status === '완료' || payload.status === '완료됨')) {
            // 원본 데이터 다시 수집하여 하위 태스크 상태 변경 반영
            collectOriginalTaskData();
          }
          
          hideEditForm();
        } else {
          alert('저장 실패: ' + (data.error || '오류'));
        }
      } catch (err) {
        alert('저장 중 오류 발생: ' + err);
      }
    });
  }
});
