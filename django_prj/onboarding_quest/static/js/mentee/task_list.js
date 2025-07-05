// mentee/task_list.js

document.addEventListener('DOMContentLoaded', function() {
  // 카드별 상세 데이터 샘플
  const details = [
    {
      title: '회사 소개 및 조직도 이해하기',
      xp: '50 XP',
      desc: '회사의 비전, 미션, 조직 구조를 파악하고 팀원들과 인사하기',
      week: '1개월차 1주차',
      badge: { text: '초급', color: 'green' },
      status: '진행중',
      list: ['회사 소개 영상 시청', '조직도 열람', '팀원 인사'],
      subtasks: [
        {
          title: '업무 환경 설정 및 도구 익히기',
          desc: '개발 환경, 툴 설치, 사내 시스템 접근 안내',
          week: '1개월차 2주차',
          badge: { text: '초급', color: 'yellow' },
          status: '진행중',
          list: ['개발 환경 설치', '사내 시스템 계정 발급'],
        },
        {
          title: '코드 컨벤션 숙지',
          desc: '팀 내 코드 스타일, 리뷰 프로세스 안내',
          week: '1개월차 2주차',
          badge: { text: '초급', color: 'green' },
          status: '진행중',
          list: ['코딩 규칙 문서 읽기', '리뷰 예시 확인'],
        },
      ],
    },
    {
      title: '첫 번째 프로젝트 참여하기',
      xp: '100 XP',
      desc: '간단한 프로젝트에 참여하여 워크플로우 이해하기',
      week: '1개월차 3주차',
      badge: { text: '중급', color: 'yellow' },
      status: '완료됨',
      list: ['프로젝트 준비', '첫 프로젝트 진행', '프로젝트 결과 공유'],
      subtasks: [
        {
          title: '프로젝트 환경 세팅',
          desc: '프로젝트 저장소 클론, 의존성 설치',
          week: '1개월차 3주차',
          badge: { text: '중급', color: 'yellow' },
          status: '진행중',
          list: ['저장소 클론', '패키지 설치'],
        },
      ],
    },
  ];

  // 상세 정보 업데이트 함수
  function updateDetail(idx, subIdx = null) {
    let d = details[idx];
    if (subIdx !== null && d.subtasks && d.subtasks[subIdx]) {
      d = d.subtasks[subIdx];
    }
    document.getElementById('detail-title').textContent = d.title;
    document.getElementById('detail-xp').textContent = d.xp || '';
    document.getElementById('detail-desc').textContent = d.desc;
    document.getElementById('detail-week').textContent = d.week;
    document.getElementById('detail-badge').textContent = d.badge.text;
    document.getElementById('detail-badge').className = 'task-badge ' + d.badge.color;
    document.getElementById('detail-status').textContent = d.status || '';
    // 리스트
    const ul = document.createElement('ul');
    (d.list || []).forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      ul.appendChild(li);
    });
    const listDiv = document.getElementById('detail-list');
    listDiv.innerHTML = '';
    listDiv.appendChild(ul);
  }
  // 카드 클릭
  const cards = document.querySelectorAll('.task-card');
  cards.forEach((card, idx) => {
    card.addEventListener('click', function() {
      cards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      updateDetail(idx);
    });
  });
  // 하위 태스크 토글
  const toggles = document.querySelectorAll('.subtask-toggle');
  toggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.stopPropagation();
      const idx = toggle.getAttribute('data-toggle');
      const list = document.getElementById('subtask-list-' + idx);
      if (list.classList.contains('open')) {
        list.classList.remove('open');
        toggle.textContent = '▼';
      } else {
        list.classList.add('open');
        toggle.textContent = '▲';
      }
    });
  });
  // 하위 태스크 클릭 시 상세 표시
  const subtaskCards = document.querySelectorAll('.subtask-card');
  subtaskCards.forEach(card => {
    card.addEventListener('click', function(e) {
      e.stopPropagation();
      const [parentIdx, subIdx] = card.getAttribute('data-detail').split('-').map(Number);
      // 상위 카드 선택 표시
      cards.forEach(c => c.classList.remove('selected'));
      cards[parentIdx].classList.add('selected');
      updateDetail(parentIdx, subIdx);
    });
  });
  // 최초 로딩 시 첫 번째 카드 상세 표시
  updateDetail(0);
});
