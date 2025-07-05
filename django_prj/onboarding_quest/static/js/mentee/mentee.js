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