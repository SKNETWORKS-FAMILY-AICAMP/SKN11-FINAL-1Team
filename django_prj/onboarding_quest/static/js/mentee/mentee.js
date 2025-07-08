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
      
      // 페이지 이동
      window.location.href = '/common/task_add/';
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
document.addEventListener('DOMContentLoaded', function() {
  initializeKanbanCards();
});

document.addEventListener('click', function(e) {
  if (!document.querySelector('.filter-dropdown').contains(e.target)) {
    document.querySelector('.filter-dropdown').classList.remove('open');
    document.getElementById('filter-menu').classList.remove('show');
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