const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');
const toggleIcon = document.getElementById('sidebarToggleIcon');
const alarmPanel = document.getElementById('alarmPanel');
let sidebarOpen = true;

if (toggleBtn && sidebar && mainContent && toggleIcon) {
    toggleBtn.addEventListener('click', () => {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            // 사이드바 펼치기
            sidebar.style.width = '18rem';
            sidebar.classList.remove('sidebar-collapsed');
            mainContent.style.marginLeft = '18rem';
            // 알람 패널 위치도 조정
            if (alarmPanel) {
                alarmPanel.style.left = '18rem';
            }
            // 펼쳐진 상태: 햄버거 메뉴 아이콘
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 6h16M4 12h16M4 18h16' />`;
        } else {
            // 사이드바 접기
            sidebar.style.width = '4rem';
            sidebar.classList.add('sidebar-collapsed');
            mainContent.style.marginLeft = '4rem';
            // 알람 패널 위치도 조정
            if (alarmPanel) {
                alarmPanel.style.left = '4rem';
            }
            // 접힌 상태: 화살표 아이콘 (펼치기)
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 5l7 7-7 7' />`;
        }
    });
}

// 알람 패널 기능
const alarmToggle = document.getElementById('alarmToggle');
const alarmOverlay = document.getElementById('alarmOverlay');
const alarmClose = document.getElementById('alarmClose');
const alarmList = document.getElementById('alarmList');
const alarmBadge = document.getElementById('alarmBadge');
let alarmPanelOpen = false; // 알람 패널 상태 추적

// 알람 패널 열기/닫기 토글
if (alarmToggle) {
    alarmToggle.addEventListener('click', () => {
        if (alarmPanelOpen) {
            closeAlarmPanel();
        } else {
            openAlarmPanel();
            loadAlarms();
        }
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
        // 사이드바 뒤에서 나오는 효과를 위해 초기 위치를 사이드바 아래쪽으로 설정
        alarmPanel.style.transform = 'translateX(-100%)';
        alarmPanel.style.zIndex = '40';
        setTimeout(() => {
            alarmPanel.style.transform = 'translateX(0)';
        }, 10);
        alarmPanelOpen = true; // 상태 업데이트
    }
}

function closeAlarmPanel() {
    if (alarmPanel && alarmOverlay) {
        // 사이드바 뒤로 사라지는 효과
        alarmPanel.style.transform = 'translateX(-100%)';
        setTimeout(() => {
            alarmPanel.classList.add('hidden');
            alarmOverlay.classList.add('hidden');
        }, 300);
        alarmPanelOpen = false; // 상태 업데이트
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
        <div class="bg-white border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors ${alarm.is_active ? 'border-l-4 border-l-blue-500' : 'opacity-60'}">
            <div class="flex items-start justify-between gap-3">
                <div class="flex items-start gap-3 flex-1 min-w-0">
                    <div class="w-2 h-2 ${alarm.is_active ? 'bg-blue-500' : 'bg-gray-300'} rounded-full mt-2 flex-shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm ${alarm.is_active ? 'text-gray-900 font-medium' : 'text-gray-500'} break-words">${alarm.message}</p>
                        <p class="text-xs text-gray-500 mt-1">${formatDate(alarm.created_at)}</p>
                    </div>
                </div>
                <div class="flex items-center gap-1 flex-shrink-0">
                    <button onclick="toggleAlarmStatus(${alarm.id}, ${!alarm.is_active})" 
                            class="p-1 rounded-full text-xs transition-colors ${alarm.is_active ? 'text-blue-600 hover:bg-blue-50' : 'text-gray-400 hover:bg-gray-50'}" 
                            title="${alarm.is_active ? '읽음으로 표시' : '읽지않음으로 표시'}">
                        ${alarm.is_active ? 
                            '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>' : 
                            '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
                        }
                    </button>
                    <button onclick="deleteAlarm(${alarm.id})" 
                            class="p-1 rounded-full text-xs text-red-400 hover:text-red-600 hover:bg-red-50 transition-colors" 
                            title="알림 삭제">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    // 모든 알림 읽음 처리 버튼 추가
    const hasActiveAlarms = alarms.some(alarm => alarm.is_active);
    const headerHTML = hasActiveAlarms ? `
        <div class="flex justify-between items-center mb-3 pb-3 border-b border-gray-200">
            <span class="text-sm font-medium text-gray-700">알림 목록</span>
            <button onclick="markAllAlarmsRead()" 
                    class="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
                    title="모든 알림 읽음 처리">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </button>
        </div>
    ` : '';
    
    alarmList.innerHTML = headerHTML + alarmHTML;
}

// 알람 상태 토글
function toggleAlarmStatus(alarmId, isActive) {
    fetch(`/api/alarms/${alarmId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ is_active: isActive })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 알람 목록 새로고침
            loadAlarms();
        } else {
            alert('알림 상태 변경에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('알람 상태 변경 실패:', error);
        alert('알림 상태 변경에 실패했습니다.');
    });
}

// 알람 삭제
function deleteAlarm(alarmId) {
    if (!confirm('이 알림을 삭제하시겠습니까?')) {
        return;
    }
    
    fetch(`/api/alarms/${alarmId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 알람 목록 새로고침
            loadAlarms();
        } else {
            alert('알림 삭제에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('알람 삭제 실패:', error);
        alert('알림 삭제에 실패했습니다.');
    });
}

// 모든 알람 읽음 처리
function markAllAlarmsRead() {
    fetch('/api/alarms/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 알람 목록 새로고침
            loadAlarms();
        } else {
            alert('알림 읽음 처리에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('알람 읽음 처리 실패:', error);
        alert('알림 읽음 처리에 실패했습니다.');
    });
}

// CSRF 토큰 가져오기
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

// 테스트 알람 생성 (관리자용)
function createTestAlarm() {
    const messages = [
        '새로운 과제가 할당되었습니다.',
        '멘토가 피드백을 남겼습니다.',
        '과제 마감일이 임박했습니다.',
        '새로운 문서가 업로드되었습니다.',
        '멘토쉽 세션이 예약되었습니다.'
    ];
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    
    fetch('/api/alarms/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ message: randomMessage })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 알람 목록 새로고침
            loadAlarms();
            alert('테스트 알림이 생성되었습니다.');
        } else {
            alert('알림 생성에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('알람 생성 실패:', error);
        alert('알림 생성에 실패했습니다.');
    });
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
    
    // 주기적으로 알람 개수 업데이트 (30초마다)
    setInterval(() => {
        fetch('/api/alarms/count/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateAlarmBadge(data.count);
                }
            })
            .catch(error => {
                console.error('알람 개수 업데이트 실패:', error);
            });
    }, 30000);
});