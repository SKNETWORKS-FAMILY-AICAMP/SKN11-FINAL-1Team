function toggleFilterMenu() {
  document.querySelector('.filter-dropdown').classList.toggle('open');
  document.getElementById('filter-menu').classList.toggle('show');
}



function selectFilter(filterType, displayText) {
  document.querySelectorAll('.filter-option').forEach(opt => opt.classList.remove('selected'));
  event.target.classList.add('selected');
  document.getElementById('current-filter').textContent = displayText;
  filterTasks(filterType);
  document.querySelector('.filter-dropdown').classList.remove('open');
  document.getElementById('filter-menu').classList.remove('show');
}

function filterTasks(period) {
  const currentDate = new Date('2025-07-04');
  document.querySelectorAll('.kanban-card').forEach(card => {
    const taskDate = new Date(card.dataset.date);
    let showCard = true;
    if (period === 'day') {
      showCard = taskDate.toDateString() === currentDate.toDateString();
    } else if (period === 'week') {
      const weekAgo = new Date(currentDate); weekAgo.setDate(weekAgo.getDate() - 7);
      showCard = taskDate >= weekAgo;
    } else if (period === 'month') {
      const monthAgo = new Date(currentDate); monthAgo.setMonth(monthAgo.getMonth() - 1);
      showCard = taskDate >= monthAgo;
    }
    card.style.display = showCard ? 'block' : 'none';
  });
}

// 카드 선택 및 상호작용 기능
function initializeKanbanCards() {
  document.querySelectorAll('.kanban-card').forEach(card => {
    // 카드 클릭 시 선택 효과 추가
    card.addEventListener('click', function(e) {
      // 다른 모든 카드의 selected 클래스 제거
      document.querySelectorAll('.kanban-card').forEach(c => c.classList.remove('selected'));
      // 현재 카드에 selected 클래스 추가
      this.classList.add('selected');
      
      // 해당 태스크 페이지 이동
      // window.location.href = 
    });
    
    // 카드 호버 시 임시 선택 효과
    card.addEventListener('mouseenter', function(e) {
      if (!this.classList.contains('selected')) {
        this.style.borderLeftWidth = '4px';
        this.style.borderLeftStyle = 'solid';
        
        // 컬럼별 색상 적용
        const column = this.closest('.kanban-column');
        if (column.classList.contains('todo-column')) {
          this.style.borderLeftColor = '#6b7280';
        } else if (column.classList.contains('processing-column')) {
          this.style.borderLeftColor = '#f59e0b';
        } else if (column.classList.contains('review-request-column')) {
          this.style.borderLeftColor = '#dc2626';
        } else if (column.classList.contains('success-column')) {
          this.style.borderLeftColor = '#10b981';
        }
      }
    });
    
    card.addEventListener('mouseleave', function(e) {
      if (!this.classList.contains('selected')) {
        this.style.borderLeftColor = 'transparent';
      }
    });
  });
}

// DOM 로드 후 초기화
// document.addEventListener('DOMContentLoaded', function() {
//   initializeKanbanCards();
// });

// 주차별 그룹화 렌더링 함수
function renderTaskListGrouped(tasks) {
    const container = document.getElementById('tasklist-left');
    container.innerHTML = '';

    // 주차별 그룹화
    const groupedTasks = {};
    tasks.forEach(task => {
        const week = task.week || 0;
        if (!groupedTasks[week]) groupedTasks[week] = [];
        groupedTasks[week].push(task);
    });

    // 주차별 섹션 생성
    Object.keys(groupedTasks).sort((a, b) => a - b).forEach(week => {
        const weekSection = document.createElement('div');
        weekSection.className = 'week-section';
        weekSection.innerHTML = `<h3>${week}주차</h3>`;

        groupedTasks[week].forEach(task => {
            const card = document.createElement('div');
            card.className = 'task-card';
            card.dataset.status = task.status;
            card.dataset.priority = task.priority;
            card.dataset.date = task.scheduled_end_date || '';
            card.dataset.week = task.week || '';

            card.innerHTML = `
                <div class="task-card-header">
                    <span class="status-badge">${task.status}</span>
                    <span class="task-title">${task.title}</span>
                </div>
                <div class="task-desc">${task.description || ''}</div>
            `;
            weekSection.appendChild(card);
        });

        container.appendChild(weekSection);
    });

    console.log(`✅ 태스크 ${tasks.length}개 주차별 렌더링 완료`);
}

function initializeFilterAndSort(mentorshipId) {
    const sortSelect = document.getElementById('task-sort');
    const statusSelect = document.getElementById('task-filter-status');
    const prioritySelect = document.getElementById('task-filter-priority');

    async function fetchTaskList() {
        const sortOption = sortSelect.value;
        const statusOption = statusSelect.value;
        const priorityOption = prioritySelect.value;

        let url = `http://127.0.0.1:8001/api/tasks/assigns?mentorship_id=${mentorshipId}`;
        if (statusOption !== 'all') url += `&status=${encodeURIComponent(statusOption)}`;
        if (priorityOption !== 'all') url += `&priority=${encodeURIComponent(priorityOption)}`;
        url += `&sort=${sortOption}`;

        console.log("▶ API 호출:", url);

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('태스크 목록 불러오기 실패');
            let data = await response.json();
            console.log("받은 데이터:", data);

            renderTaskListGrouped(data);
        } catch (err) {
            console.error('❌ API 호출 오류:', err);
        }
    }

    sortSelect.addEventListener('change', fetchTaskList);
    statusSelect.addEventListener('change', fetchTaskList);
    prioritySelect.addEventListener('change', fetchTaskList);

    fetchTaskList();
    console.log('✅ 필터/정렬 기능 설정 완료');
}

document.addEventListener('DOMContentLoaded', () => {
    const mentorshipId = document.getElementById('tasklist-left')?.dataset.mentorshipId;
    console.log("mentorshipId:", mentorshipId);
    initializeFilterAndSort(mentorshipId);
    
});

document.addEventListener('DOMContentLoaded', () => {
  const completionText = document.getElementById('userLevelTop');
  const completeBtn = document.getElementById('final-complete-btn');

  if (completionText && completeBtn) {
    const percentage = parseInt(completionText.textContent.replace('%', ''), 10);
    if (percentage === 100) {
      completeBtn.style.display = 'inline-block';
    }
  }
});

function completeFinalTask() {
  alert('🎉 모든 작업을 완료했습니다!');
  // 필요 시 서버로 완료 상태 전송 API 추가 가능
}



document.addEventListener('click', function(e) {
  const filterDropdown = document.querySelector('.filter-dropdown');
  const filterMenu = document.getElementById('filter-menu');
  
  // 요소가 존재하는 경우에만 실행
  if (filterDropdown && filterMenu) {
    if (!filterDropdown.contains(e.target)) {
      filterDropdown.classList.remove('open');
      filterMenu.classList.remove('show');
    }
  }
});

document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
  cb.addEventListener('change', function () {
    const label = this.nextElementSibling;
    label.style.textDecoration = this.checked ? 'line-through' : 'none';
    label.style.color = this.checked ? '#6c757d' : '#495057';
  });
});

// 초기 상태 반영
document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
  const label = cb.nextElementSibling;
  label.style.textDecoration = 'line-through';
  label.style.color = '#6c757d';
});