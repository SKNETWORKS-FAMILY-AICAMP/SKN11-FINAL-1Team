// 공용 커리큘럼 체크박스 체크 상태 JS로 처리
document.addEventListener('DOMContentLoaded', function() {
  if (window.edit_mode && window.curriculum && window.curriculum.is_common) {
    document.getElementById('is-public-curriculum').checked = true;
  } else {
    document.getElementById('is-public-curriculum').checked = false;
  }
});
// edit_mode, curriculum, tasks_json이 context로 전달될 경우 window에 할당
// edit_mode가 'True', 'true', '1' 등 다양한 값으로 올 수 있으니 모두 True로 인식
window.edit_mode = ["true", "True", "1"].includes("{{ edit_mode|default:'false' }}");
window.curriculum = JSON.parse('{{ curriculum|escapejs|default:"null" }}');
window.tasks_json = JSON.parse('{{ tasks_json|escapejs|default:"[]" }}');

// 커리큘럼 초안 생성 함수 (텍스트 추가)
function generateDraftContent() {
  const curriculumTextarea = document.getElementById('curriculum-textarea');
  const draftContent = `# week1 조직문화 이해 및 관찰
# week2 조직문화 실천 체험
# week3 조직문화 실천 체험 발표 및 피드백
# week4 팀워크 향상 프로그램 참여
# week5 조직 내 비공식 커뮤니케이션 탐색
# week6 사내 이벤트 참여 후기 작성
# week7 동료 피드백 수렴 및 자기성찰
# week8 사내 이슈 브리핑 참여
# week9 부서 간 협업 업무 참여
# week10 회사 미션/비전 재해석 활동
# week11 역멘토링 활동
# week12 평생 신입사원 되기 프로젝트`;
  curriculumTextarea.value = draftContent;
}

// 세부 Task 생성 토글 함수
function toggleTaskSection() {
  const taskList = document.getElementById('task-list');
  if (taskList.style.display === 'none') {
    taskList.style.display = 'flex';
  } else {
    taskList.style.display = 'none';
  }
}

// Drag & Drop for task list
function initTaskListDnD() {
  const taskList = document.getElementById('task-list');
  let draggingEl = null;
  let dragOverEl = null;
  Array.from(taskList.children).forEach(item => {
    item.addEventListener('dragstart', e => {
      draggingEl = item;
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    item.addEventListener('dragend', e => {
      draggingEl = null;
      item.classList.remove('dragging');
      Array.from(taskList.children).forEach(i => i.classList.remove('drag-over'));
    });
    item.addEventListener('dragover', e => {
      e.preventDefault();
    });
    item.addEventListener('dragenter', e => {
      if (item !== draggingEl) {
        item.classList.add('drag-over');
        dragOverEl = item;
      }
    });
    item.addEventListener('dragleave', e => {
      item.classList.remove('drag-over');
      dragOverEl = null;
    });
    item.addEventListener('drop', e => {
      e.preventDefault();
      if (item !== draggingEl) {
        item.classList.remove('drag-over');
        // 순서 변경
        const children = Array.from(taskList.children);
        const dropIdx = children.indexOf(item);
        taskList.removeChild(draggingEl);
        if (dropIdx < children.length - 1) {
          taskList.insertBefore(draggingEl, item);
        } else {
          taskList.appendChild(draggingEl);
        }
      }
    });
  });
}

// edit_mode일 때 폼 자동 채우기
document.addEventListener('DOMContentLoaded', function() {
  const taskList = document.getElementById('task-list');

  // 주차별로 그룹핑하여 카드 렌더링
  function renderTasksByWeek(tasks) {
    // week 기준 그룹핑
    const weekMap = {};
    tasks.forEach(task => {
      const week = task.week || 1;
      if (!weekMap[week]) weekMap[week] = [];
      weekMap[week].push(task);
    });
    // 주차 오름차순 정렬
    const sortedWeeks = Object.keys(weekMap).sort((a, b) => a - b);
    taskList.innerHTML = '';
    sortedWeeks.forEach(week => {
      const weekTasks = weekMap[week];
      // 주차별 영역
      const weekSection = document.createElement('div');
      weekSection.className = 'week-section';
      // 주차 헤더
      const weekHeader = document.createElement('div');
      weekHeader.style = 'font-weight:bold; font-size:1.1em; margin-bottom:10px; color:#7c5c1e;';
      weekHeader.textContent = `${week}주차`;
      weekSection.appendChild(weekHeader);
      // 각 Task 카드
      weekTasks.forEach(task => {
        const item = document.createElement('div');
        item.className = 'template-task-item';
        item.setAttribute('draggable', 'true');
        item.innerHTML = `
          <div class="task-content">
            <div class="task-badges">
              <span class="task-badge difficulty-${task.priority === '상' ? 'high' : (task.priority === '중' ? 'medium' : 'low')}" >${task.priority || '하'}</span>
              ${task.period ? `<span class='task-badge exp-badge'>${task.period}일</span>` : ''}
            </div>
            <div style="font-weight:bold; color:#222;">${task.title || ''}</div>
            ${task.guideline ? `<div style='color:#1976d2; font-size:13px;'>가이드: ${task.guideline}</div>` : ''}
            ${task.description ? `<div style='color:#555; font-size:13px;'>설명: ${task.description}</div>` : ''}
          </div>
        `;
        weekSection.appendChild(item);
      });
      taskList.appendChild(weekSection);
    });
    taskList.style.display = 'flex';
  }

  if (window.edit_mode && window.curriculum) {
    document.querySelector('input.tasklist-search').value = window.curriculum.curriculum_title || '';
    document.getElementById('curriculum-desc').value = window.curriculum.curriculum_description || '';
    document.getElementById('curriculum-textarea').value = window.curriculum.week_schedule || '';

    if (Array.isArray(window.tasks_json) && window.tasks_json.length > 0) {
      renderTasksByWeek(window.tasks_json);
    } else {
      taskList.style.display = 'none';
    }
    initTaskListDnD();
  } 
  else {
    initTaskListDnD();
  }
});