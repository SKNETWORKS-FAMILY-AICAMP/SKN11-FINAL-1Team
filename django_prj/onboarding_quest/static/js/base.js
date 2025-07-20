const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');
const toggleIcon = document.getElementById('sidebarToggleIcon');
let sidebarOpen = true;

if (toggleBtn && sidebar && mainContent && toggleIcon) {
    toggleBtn.addEventListener('click', () => {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            // 사이드바 펼치기
            sidebar.style.width = '18rem';
            sidebar.classList.remove('sidebar-collapsed');
            mainContent.style.marginLeft = '18rem';
            // 펼쳐진 상태: 햄버거 메뉴 아이콘
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 6h16M4 12h16M4 18h16' />`;
        } else {
            // 사이드바 접기
            sidebar.style.width = '4rem';
            sidebar.classList.add('sidebar-collapsed');
            mainContent.style.marginLeft = '4rem';
            // 접힌 상태: 화살표 아이콘 (펼치기)
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 5l7 7-7 7' />`;
        }
    });
}

// 알람 패널 기능
const alarmToggle = document.getElementById('alarmToggle');
const alarmPanel = document.getElementById('alarmPanel');
const alarmOverlay = document.getElementById('alarmOverlay');
const alarmClose = document.getElementById('alarmClose');
const alarmList = document.getElementById('alarmList');
const alarmBadge = document.getElementById('alarmBadge');

// 알람 패널 열기
if (alarmToggle) {
    alarmToggle.addEventListener('click', () => {
        openAlarmPanel();
        loadAlarms();
    });
}

// 알람 패널 닫기
if (alarmClose) {
    alarmClose.addEventListener('click', closeAlarmPanel);
}

if (alarmOverlay) {
    alarmOverlay.addEventListener('click', closeAlarmPanel);
}

function openAlarmPanel() {
    if (alarmPanel && alarmOverlay) {
        alarmPanel.classList.remove('hidden');
        alarmOverlay.classList.remove('hidden');
        setTimeout(() => {
            alarmPanel.style.transform = 'translateX(0)';
        }, 10);
    }
}

function closeAlarmPanel() {
    if (alarmPanel && alarmOverlay) {
        alarmPanel.style.transform = 'translateX(100%)';
        setTimeout(() => {
            alarmPanel.classList.add('hidden');
            alarmOverlay.classList.add('hidden');
        }, 300);
    }
}

// 알람 목록 로드
function loadAlarms() {
    // AJAX로 알람 목록을 가져와서 표시
    fetch('/api/alarms/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAlarms(data.alarms);
                updateAlarmBadge(data.count);
            } else {
                throw new Error(data.error || '알람 로드 실패');
            }
        })
        .catch(error => {
            console.error('알람 로드 실패:', error);
            if (alarmList) {
                alarmList.innerHTML = `
                    <div class="text-center text-red-500 py-8">
                        <p>알림을 불러오는데 실패했습니다</p>
                    </div>
                `;
            }
        });
}

// 알람 목록 표시
function displayAlarms(alarms) {
    if (!alarmList) return;
    
    if (alarms.length === 0) {
        alarmList.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                </svg>
                <p>새로운 알림이 없습니다</p>
            </div>
        `;
        return;
    }
    
    const alarmHTML = alarms.map(alarm => `
        <div class="bg-white border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
            <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm text-gray-900 break-words">${alarm.message}</p>
                    <p class="text-xs text-gray-500 mt-1">${formatDate(alarm.created_at)}</p>
                </div>
            </div>
        </div>
    `).join('');
    
    alarmList.innerHTML = alarmHTML;
}

// 알람 뱃지 업데이트
function updateAlarmBadge(count) {
    if (!alarmBadge) return;
    
    if (count > 0) {
        alarmBadge.textContent = count > 99 ? '99+' : count;
        alarmBadge.classList.remove('hidden');
    } else {
        alarmBadge.classList.add('hidden');
    }
}

// 날짜 포맷팅
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // 1분 미만
        return '방금 전';
    } else if (diff < 3600000) { // 1시간 미만
        return `${Math.floor(diff / 60000)}분 전`;
    } else if (diff < 86400000) { // 24시간 미만
        return `${Math.floor(diff / 3600000)}시간 전`;
    } else {
        return date.toLocaleDateString('ko-KR');
    }
}

// 페이지 로드 시 알람 개수 확인
document.addEventListener('DOMContentLoaded', () => {
    // 알람 개수만 먼저 로드
    fetch('/api/alarms/count/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateAlarmBadge(data.count);
            }
        })
        .catch(error => {
            console.error('알람 개수 로드 실패:', error);
        });
});