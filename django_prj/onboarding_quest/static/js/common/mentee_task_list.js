// mentee_task_list.js

// 현재 선택된 태스크 정보
let currentTaskId = null;
let currentTaskData = null;

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

// 🔧 가이드라인 표시 함수
function displayGuideline(taskData) {
  const guidelineContent = document.getElementById('guideline-content');
  if (guidelineContent && taskData) {
    const guideline = taskData.guideline || '가이드라인이 없습니다.';
    guidelineContent.textContent = guideline;
  } else {
    console.error('❌ guidelineContent 또는 taskData가 없음');
  }
}

// 🔧 메모 로드 함수
async function loadMemos(taskId) {
  try {
    const response = await fetch(`/mentee/task_detail/${taskId}/`);
    const data = await response.json();
    if (data.success && data.task && data.task.memos) {
      displayMemos(data.task.memos);
    } else {
      displayMemos([]); // 빈 배열로 표시
    }
  } catch (error) {
    console.error('❌ 메모 로드 실패:', error);
    displayMemos([]); // 오류 시 빈 배열로 표시
  }
}

// 🔧 메모 표시 함수
function displayMemos(memos) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) {
    console.error('❌ chat-messages 요소를 찾을 수 없음');
    return;
  }
  chatMessages.innerHTML = '';
  if (memos && memos.length > 0) {
    memos.forEach((memo) => {
      const memoDiv = document.createElement('div');
      memoDiv.style.cssText = 'margin-bottom:12px; padding:8px; background:white; border-radius:6px; border-left:3px solid #28a745;';
      memoDiv.innerHTML = `
        <div style="font-size:12px; color:#666; margin-bottom:4px;">
          ${memo.user || '사용자'} • ${new Date(memo.create_date).toLocaleString('ko-KR')}
        </div>
        <div style="color:#333;">${memo.comment}</div>
      `;
      chatMessages.appendChild(memoDiv);
    });
  } else {
    chatMessages.innerHTML = '<div style="text-align:center; color:#999; padding:20px;">등록된 메모가 없습니다.</div>';
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 🔧 메모 저장 함수
async function saveMemo(taskId, comment) {
  try {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('input[name="csrftoken"]')?.value ||
                     getCookie('csrftoken');
    
    const response = await fetch(`/mentee/task_comment/${taskId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'Accept': 'application/json'
      },
      body: JSON.stringify({ comment: comment })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 메모 저장 성공 시 메모 목록 새로고침
      await loadMemos(taskId);
      return true;
    } else {
      console.error('메모 저장 실패:', data.error);
      showError('메모 저장에 실패했습니다: ' + (data.error || '알 수 없는 오류'));
      return false;
    }
  } catch (error) {
    console.error('메모 저장 오류:', error);
    showError('메모 저장 중 오류가 발생했습니다.');
    return false;
  }
}

// CSRF 토큰 가져오기 함수
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

// 🔧 메모 입력 기능 초기화
function initMemoInput() {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  
  if (sendBtn) {
    sendBtn.addEventListener('click', async function() {
      const comment = chatInput.value.trim();
      if (comment && currentTaskId) {
        if (await saveMemo(currentTaskId, comment)) {
          chatInput.value = '';
        }
      } else if (!comment) {
        showWarning('메모를 입력해주세요.');
      } else if (!currentTaskId) {
        showWarning('태스크를 선택해주세요.');
      }
    });
  }
  
  if (chatInput) {
    chatInput.addEventListener('keypress', async function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const comment = chatInput.value.trim();
        if (comment && currentTaskId) {
          if (await saveMemo(currentTaskId, comment)) {
            chatInput.value = '';
          }
        }
      }
    });
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
    
    // 첫 번째 태스크 자동 선택 (별도 로직으로 이동됨)
  }
  
  // 태스크 카드 이벤트 재연결
  function attachTaskCardEvents() {
    const cards = document.querySelectorAll('.task-card');
    cards.forEach(card => {
      // 기존 이벤트 리스너 제거를 위해 클론 후 교체
      const newCard = card.cloneNode(true);
      card.parentNode.replaceChild(newCard, card);
      
      newCard.addEventListener('click', function() {
        // 편집 중일 때는 클릭 차단
        if (typeof isEditing !== 'undefined' && isEditing) {
          showWarning('편집을 완료하거나 취소한 후 다른 태스크를 선택할 수 있습니다.');
          return;
        }
        
        // 🔧 selectTask 함수 사용으로 통합
        selectTask(this);
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
  
  // 🔧 메모 입력 기능 초기화
  initMemoInput();
  
  // 🔧 선택된 태스크 표시 (URL 파라미터 기반)
  setTimeout(() => {
    if (window.selectedTaskId || window.selectedTaskData) {
      console.log('🔍 페이지 로드 시 선택된 태스크 있음');
      displaySelectedTask();
    } else {
      console.log('🔍 페이지 로드 시 선택된 태스크 없음 - 첫 번째 태스크 선택');
      const firstTaskCard = document.querySelector('.task-card');
      if (firstTaskCard) {
        // URL 이동 없이 직접 표시만 (기본 동작)
        const taskId = firstTaskCard.dataset.taskId;
        if (taskId) {
          currentTaskId = taskId;
          
          // 선택 표시
          document.querySelectorAll('.task-card').forEach(card => card.classList.remove('selected'));
          firstTaskCard.classList.add('selected');
          
          // API로 상세 정보 로드
          fetch(`/mentee/task_detail/${taskId}/`)
            .then(response => response.json())
            .then(data => {
              if (data.success && data.task) {
                updateDetailFromData(data.task, false);
              }
            })
            .catch(error => {
              console.error('❌ 첫 번째 태스크 API 호출 실패:', error);
            });
        }
      }
    }
  }, 100);

  // 하위 테스크(서브태스크) 클릭 시 상세 정보 표시
  function attachSubtaskClickEvents() {
    document.querySelectorAll('.subtask-item').forEach(function(item) {
      // 기존 이벤트 리스너 제거를 위해 클론 후 교체
      const newItem = item.cloneNode(true);
      item.parentNode.replaceChild(newItem, item);
      
      newItem.addEventListener('click', function(e) {
        e.stopPropagation(); // 상위 카드 클릭 방지
        
        // 편집 중일 때는 클릭 차단
        if (typeof isEditing !== 'undefined' && isEditing) {
          showWarning('편집을 완료하거나 취소한 후 다른 태스크를 선택할 수 있습니다.');
          return;
        }
        
        const taskId = this.getAttribute('data-task-id');
        console.log(`📌 서브태스크 클릭: ${taskId}`);
        
        // 🔧 서브태스크도 새 URL로 이동
        if (taskId) {
          navigateToTask(taskId);
        }
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
    if (!currentTask) return showWarning('상위 Task를 먼저 선택하세요.');
    subtaskModal.style.display = 'flex';
    subtaskForm.reset();
    document.getElementById('subtask-parent-title').value = currentTask.title || '';
    document.getElementById('subtask-parent-id').value = currentTask.id;
    
    // 상위 Task와 동일한 우선순위 설정
    document.getElementById('subtask-priority').value = currentTask.priority || '하';
    
    // 상위 Task와 동일한 시작일/마감일 설정 (TaskAssign 필드명 사용)
    if (currentTask.scheduled_start_date) {
      document.getElementById('subtask-start-date').value = currentTask.scheduled_start_date;
    } else {
      // 시작일이 없으면 오늘 날짜로 설정
      const today = new Date().toISOString().split('T')[0];
      document.getElementById('subtask-start-date').value = today;
    }
    
    if (currentTask.scheduled_end_date) {
      document.getElementById('subtask-end-date').value = currentTask.scheduled_end_date;
    }
    
    document.getElementById('subtask-status').value = '진행 전';
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
    if (!currentTask) return showWarning('상위 Task를 먼저 선택하세요.');
    const title = document.getElementById('subtask-title').value.trim();
    const guideline = document.getElementById('subtask-guideline').value.trim();
    const description = document.getElementById('subtask-desc').value.trim();
    const status = document.getElementById('subtask-status').value;
    const priority = document.getElementById('subtask-priority').value;
    const start_date = document.getElementById('subtask-start-date').value;
    const end_date = document.getElementById('subtask-end-date').value;
    const parent_id = document.getElementById('subtask-parent-id').value;
    // 상위 Task의 mentorship_id, week, order도 전달
    const mentorship_id = currentTask.mentorship_id || (currentTask.mentorship_id || null);
    const week = currentTask.week;
    const order = null;
    if (!title) return showWarning('제목을 입력하세요.');
    try {
      const resp = await fetch(`/mentee/create_subtask/${parent_id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': (document.querySelector('input[name=csrfmiddlewaretoken]')||{}).value || ''
        },
        body: JSON.stringify({
          title, 
          guideline, 
          description, 
          status, 
          priority, 
          scheduled_start_date: start_date, 
          scheduled_end_date: end_date, 
          mentorship_id, 
          week, 
          order
        })
      });
      const data = await resp.json();
      if (data.success) {
        showSuccess('하위 테스크가 생성되었습니다.');
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
        showError('생성 실패: ' + (data.error || '오류'));
      }
    } catch (err) {
      showError('생성 중 오류: ' + err);
    }
  });
  const cards = document.querySelectorAll('.task-card');
  let currentTask = null; // 현재 선택된 task 정보 저장
  function updateDetailFromData(task, isSubtask = false) {
    currentTask = task;
    
    // 🔧 현재 선택된 태스크 정보 업데이트
    currentTaskId = task.task_assign_id || task.id;
    currentTaskData = task;
    
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
    
    // 🔧 가이드라인 표시 (새로운 구조)
    displayGuideline(task);
    
    // 🔧 메모 로드
    if (currentTaskId) {
      loadMemos(currentTaskId);
    }
    
    // guideline이 null/빈값이면 표시하지 않음 (기존 desc 영역 - 사용 안 함)
    const descEl = document.getElementById('detail-desc');
    if (descEl) {
      descEl.style.display = 'none'; // 새 구조에서는 사용하지 않음
    }
    
    // 난이도/마감일 메타
    const metaRow = document.querySelector('.task-detail-meta-row');
    let badgeClass = 'yellow';
    if (task.priority === '상') badgeClass = 'red';
    else if (task.priority === '중') badgeClass = 'green';
    
    // 시작일과 마감일 표시
    let startDateText = task.scheduled_start_date ? `시작: ${task.scheduled_start_date}` : '';
    let endDateText = task.scheduled_end_date ? `마감: ${task.scheduled_end_date}` : '';
    
    metaRow.innerHTML = `
      <span class="task-badge ${badgeClass}" id="detail-badge">${task.priority || '하'}</span> 
      <span class="d-day-badge" id="detail-dday">${endDateText}</span>
      <span class="task-date-info" id="detail-start-date">${startDateText}</span>
      <span class="task-date-info" id="detail-end-date"></span>
    `;
    
    // description을 리스트로 표시 (기존 코드 유지)
    // 하지만 새로운 구조에서는 가이드라인이 별도 영역에 표시됨
    
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
          showError('댓글 등록 실패: ' + (data.error || '오류'));
        }
      } catch (err) {
        showError('댓글 등록 중 오류: ' + err);
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
        start_date: startDate,
        end_date: endDate,
        priority: editPriority.value,
        scheduled_start_date:editStartDate.value || null,
        scheduled_end_date: editEndDate.value || null
      };

      console.log("DEBUG payload:", payload);


      // 이 부분 mentee/update_task_status로 변경했음.
      try {
        const resp = await fetch(`/mentee/update_task_status/${currentTask.id}/`, {
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
          showError('저장 실패: ' + (data.error || '오류'));
        }
      } catch (err) {
        showError('저장 중 오류 발생: ' + err);
      }
    });
  }

  // 🚀 Phase 2: 태스크 상세정보 패널 활성화 + 실시간 메시지 시스템
  let currentSelectedTaskId = null; // 전역 변수

  // ✅ 미션 4: 태스크 카드 클릭 핸들러 (기존 이벤트에 추가)
  document.addEventListener('click', function(e) {
    const taskCard = e.target.closest('.task-card');
    const subtaskItem = e.target.closest('.subtask-item');
    
    if (taskCard && !taskCard.classList.contains('selected') && !e.target.closest('.task-controls')) {
      selectTask(taskCard);
    } else if (subtaskItem) {
      selectSubtask(subtaskItem);
    }
  });

  // 🔧 태스크 클릭 시 새 URL로 이동하는 함수
  function navigateToTask(taskId) {
    const currentUrl = new URL(window.location);
    const mentorshipId = currentUrl.searchParams.get('mentorship_id') || window.mentorshipId;
    
    if (mentorshipId && taskId) {
      const newUrl = `/mentee/task_list/?mentorship_id=${mentorshipId}&task_assign_id=${taskId}`;
      console.log(`🔄 새 URL로 이동: ${newUrl}`);
      window.location.href = newUrl;
    }
  }
  
  // 🔧 태스크 선택 함수 (URL 이동 방식으로 변경)
  function selectTask(taskCard) {
    console.log('🔍 selectTask 호출:', taskCard);
    
    const taskId = taskCard.dataset.taskId;
    console.log(`📋 태스크 선택: ${taskId}`);
    
    // 🔧 새로운 방식: 새 URL로 이동
    if (taskId) {
      navigateToTask(taskId);
    }
  }
  
  // 🔧 페이지 로드 시 선택된 태스크 표시 함수
  function displaySelectedTask() {
    console.log('🔍 displaySelectedTask 호출');
    console.log('🔍 selectedTaskData:', window.selectedTaskData);
    console.log('🔍 selectedTaskId:', window.selectedTaskId);
    
    if (window.selectedTaskData) {
      // 현재 선택된 태스크 정보 업데이트
      currentTaskId = window.selectedTaskData.task_assign_id || window.selectedTaskData.id;
      currentTaskData = window.selectedTaskData;
      
      console.log('🔍 선택된 태스크로 상세 정보 업데이트:', currentTaskId);
      
      // 해당 태스크 카드에 선택 표시
      const taskCard = document.querySelector(`[data-task-id="${currentTaskId}"]`);
      if (taskCard) {
        document.querySelectorAll('.task-card').forEach(card => card.classList.remove('selected'));
        document.querySelectorAll('.subtask-item').forEach(item => item.classList.remove('selected'));
        taskCard.classList.add('selected');
        console.log('🔍 태스크 카드에 선택 표시 적용');
      }
      
      // 상세 정보 업데이트
      updateDetailFromData(window.selectedTaskData, false);
    } else if (window.selectedTaskId) {
      // selectedTaskData가 없으면 API로 조회
      console.log('🔍 selectedTaskData가 없어서 API로 조회');
      fetch(`/mentee/task_detail/${window.selectedTaskId}/`)
        .then(response => response.json())
        .then(data => {
          if (data.success && data.task) {
            currentTaskId = window.selectedTaskId;
            currentTaskData = data.task;
            
            // 해당 태스크 카드에 선택 표시
            const taskCard = document.querySelector(`[data-task-id="${window.selectedTaskId}"]`);
            if (taskCard) {
              document.querySelectorAll('.task-card').forEach(card => card.classList.remove('selected'));
              document.querySelectorAll('.subtask-item').forEach(item => item.classList.remove('selected'));
              taskCard.classList.add('selected');
            }
            
            updateDetailFromData(data.task, false);
          }
        })
        .catch(error => {
          console.error('❌ selectedTask API 호출 실패:', error);
        });
    }
  }

  // 🔧 서브태스크 선택 함수 (더 이상 사용하지 않음 - URL 이동 방식으로 변경)
  // function selectSubtask(subtaskItem) {
  //   // 서브태스크도 navigateToTask() 함수를 통해 새 URL로 이동
  // }

  // ✅ 미션 5: 메시지 전송 버튼 연결
  const messageSendBtn = document.getElementById('chat-send-btn');
  const messageInput = document.getElementById('chat-input');
  
  if (messageSendBtn) {
    messageSendBtn.addEventListener('click', sendMessage);
  }
  
  if (messageInput) {
    messageInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // 🌐 메시지 전송 함수
  async function sendMessage() {
    if (!currentSelectedTaskId) {
      showWarning('태스크를 먼저 선택해주세요.');
      return;
    }
    
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) {
      showWarning('메시지를 입력해주세요.');
      return;
    }
    
    console.log(`💬 메시지 전송: ${currentSelectedTaskId} -> "${message}"`);
    
    try {
      const response = await fetch(`/mentee/task_comment/${currentSelectedTaskId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'), // 기존 함수 활용
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ comment: message })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          chatInput.value = '';
          console.log('✅ 메시지 전송 성공');
          loadTaskMessages(currentSelectedTaskId); // 메시지 목록 새로고침
        } else {
          showError('메시지 전송 실패: ' + (data.error || '알 수 없는 오류'));
        }
      } else {
        showError('메시지 전송에 실패했습니다.');
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      showError('네트워크 오류가 발생했습니다.');
    }
  }

  // 📋 메시지 목록 로드 함수
  async function loadTaskMessages(taskId) {
    console.log(`📨 메시지 로드: ${taskId}`);
    
    try {
      const response = await fetch(`/mentee/task_detail/${taskId}/`, {
        headers: {
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.success) {
          const messagesContainer = document.getElementById('chat-messages');
          if (!messagesContainer) return;
          
          messagesContainer.innerHTML = '';
          
          const memos = data.task.memos || [];
          console.log(`💬 메시지 개수: ${memos.length}`);
          
          if (memos.length === 0) {
            messagesContainer.innerHTML = '<div style="color: #999; text-align: center; padding: 20px; font-style: italic;">아직 댓글이 없습니다.</div>';
          } else {
            memos.forEach(memo => {
              const messageDiv = document.createElement('div');
              messageDiv.className = 'message';
              messageDiv.style.cssText = 'margin-bottom: 12px; padding: 8px; background: #f5f5f5; border-radius: 6px; font-size: 14px;';
              
              messageDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <div>
                    <strong style="color: #333;">${memo.user || '익명'}</strong>: ${memo.comment || ''}
                  </div>
                  <small style="color: #666; font-size: 12px; white-space: nowrap; margin-left: 10px;">
                    ${memo.create_date || ''}
                  </small>
                </div>
              `;
              
              messagesContainer.appendChild(messageDiv);
            });
          }
          
          // 자동 스크롤 (최신 메시지로)
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
          
        } else {
          console.error('메시지 로드 실패:', data.error);
        }
      } else {
        console.error('메시지 로드 HTTP 오류:', response.status);
      }
    } catch (error) {
      console.error('메시지 로드 예외:', error);
    }
  }

  // 🛠️ CSRF 토큰 가져오기 함수 (기존 로직 재사용)
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

  // 🚀 초기 선택: 선택된 태스크 처리 (위에서 처리됨)
  
});
