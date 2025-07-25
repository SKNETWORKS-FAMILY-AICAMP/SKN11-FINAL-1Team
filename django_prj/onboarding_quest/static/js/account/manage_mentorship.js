let currentMentorshipId = null;

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

function getCSRFToken() {
    // 먼저 메타 태그에서 가져오기
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // 폼의 CSRF 토큰 가져오기
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    
    // 마지막으로 쿠키에서 가져오기
    return getCookie('csrftoken');
}

function searchMentorships() {
    const searchTerm = document.getElementById('search-input').value;
    const statusFilter = document.getElementById('status-filter').value;
    const departmentFilter = document.getElementById('department-filter').value;
    
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (statusFilter) params.append('status', statusFilter);
    if (departmentFilter) params.append('department', departmentFilter);
    
    window.location.href = `?${params.toString()}`;
}

// 실시간 필터링 함수
function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    const departmentFilter = document.getElementById('department-filter').value;
    
    const tableRows = document.querySelectorAll('#mentorship-table tbody tr');
    
    tableRows.forEach(row => {
        let shouldShow = true;
        
        // 이름 검색 필터
        if (searchTerm) {
            const mentorName = row.cells[1].textContent.trim().toLowerCase();
            const menteeName = row.cells[2].textContent.trim().toLowerCase();
            
            if (!mentorName.includes(searchTerm) && !menteeName.includes(searchTerm)) {
                shouldShow = false;
            }
        }
        
        // 상태 필터
        if (statusFilter && shouldShow) {
            const statusCell = row.cells[5]; // 상태 컬럼
            const statusText = statusCell.textContent.trim();
            
            if (statusFilter === 'active' && !statusText.includes('활성')) {
                shouldShow = false;
            } else if (statusFilter === 'inactive' && !statusText.includes('비활성')) {
                shouldShow = false;
            }
        }
        
        // 부서 필터
        if (departmentFilter && shouldShow) {
            const mentorDept = row.cells[1].querySelector('div:last-child')?.textContent.trim() || '';
            const menteeDept = row.cells[2].querySelector('div:last-child')?.textContent.trim() || '';
            
            // 선택된 부서명을 찾기
            const selectedDeptOption = document.querySelector(`#department-filter option[value="${departmentFilter}"]`);
            const selectedDeptName = selectedDeptOption ? selectedDeptOption.textContent : '';
            
            if (!mentorDept.includes(selectedDeptName) && !menteeDept.includes(selectedDeptName)) {
                shouldShow = false;
            }
        }
        
        // 행 표시/숨김
        row.style.display = shouldShow ? '' : 'none';
    });
    
    // 필터링 결과 업데이트
    updateFilterResults();
}

// 필터링 결과 통계 업데이트
function updateFilterResults() {
    const tableRows = document.querySelectorAll('#mentorship-table tbody tr');
    const visibleRows = Array.from(tableRows).filter(row => row.style.display !== 'none');
    
    console.log(`필터링 결과: ${visibleRows.length}/${tableRows.length} 개의 멘토십이 표시됩니다.`);
}

// 비활성화된 멘토쉽 아래로 내리기
function reorderRows() {
    const tbody = document.querySelector('#mentorship-table tbody');
    if (!tbody) return;
    Array.from(tbody.querySelectorAll('tr')).forEach(row => {
        const statusCell = row.cells[5];
        const statusText = statusCell ? statusCell.textContent.trim() : '';
        if (statusText.includes('비활성')) {
            tbody.appendChild(row);
        }
    });
}

// 페이지 로드 시 초기 필터 적용
document.addEventListener('DOMContentLoaded', function() {
    // 초기 필터 적용 (URL 파라미터가 있는 경우)
    applyFilters();
    // 비활성 항목은 하단으로 이동
    reorderRows();

    // 검색 입력 시 엔터키 처리
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMentorships();
            }
        });
    }
});

function editMentorship(mentorshipId) {
    currentMentorshipId = mentorshipId;
    
    // AJAX로 멘토쉽 정보 가져오기
    fetch(`/account/mentorship/${mentorshipId}/detail/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('edit-mentor').value = data.mentor_id || '';
            document.getElementById('edit-mentee').value = data.mentee_id || '';
            document.getElementById('edit-start-date').value = data.start_date || '';
            document.getElementById('edit-end-date').value = data.end_date || '';
            document.getElementById('edit-curriculum').value = data.curriculum_id || '';
            // is_active 값을 사용하여 실제 활성 상태 표시 (boolean or string)
            const rawIsActive = data.is_active;
            const isActive = rawIsActive === true || rawIsActive === 'True' || rawIsActive === 'true';
            document.getElementById('edit-status').value = isActive ? 'true' : 'false';
            console.log('Raw is_active:', rawIsActive, ', parsed isActive:', isActive);
            
            document.getElementById('edit-modal').classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error fetching mentorship data:', error);
            alert('멘토쉽 정보를 가져오는 중 오류가 발생했습니다.');
        });
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
    currentMentorshipId = null;
}

function saveMentorship() {
    // 로딩 상태 표시
    const saveBtn = document.getElementById('save-btn');
    const saveText = saveBtn.querySelector('.save-text');
    const loadingSpinner = saveBtn.querySelector('.loading-spinner');
    
    saveBtn.disabled = true;
    saveText.style.display = 'none';
    loadingSpinner.style.display = 'inline';
    
    const formData = {
        mentor_id: document.getElementById('edit-mentor').value,
        mentee_id: document.getElementById('edit-mentee').value,
        curriculum_id: document.getElementById('edit-curriculum').value,
        start_date: document.getElementById('edit-start-date').value,
        end_date: document.getElementById('edit-end-date').value,
        is_active: document.getElementById('edit-status').value === 'true'
        
    };
    
    console.log('Sending mentorship update request:', {
        mentorshipId: currentMentorshipId,
        url: `/account/mentorship/${currentMentorshipId}/edit/`,
        data: formData
    });
    
    fetch(`/account/mentorship/${currentMentorshipId}/edit/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            // 모달 닫기
            closeEditModal();
            // 페이지 새로고침으로 변경사항 즉시 반영
            window.location.reload();
        } else {
            alert('저장 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('Error saving mentorship:', error);
        alert('저장 중 오류가 발생했습니다: ' + error.message);
        
        // 로딩 상태 해제
        const saveBtn = document.getElementById('save-btn');
        const saveText = saveBtn.querySelector('.save-text');
        const loadingSpinner = saveBtn.querySelector('.loading-spinner');
        
        saveBtn.disabled = false;
        saveText.style.display = 'inline';
        loadingSpinner.style.display = 'none';
    });
}

function deleteMentorship(mentorshipId) {
    if (confirm('정말로 이 멘토쉽을 삭제하시겠습니까?')) {
        fetch(`/account/mentorship/${mentorshipId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('멘토쉽이 성공적으로 삭제되었습니다.');
                // 페이지 새로고침으로 변경사항 즉시 반영
                window.location.reload();
            } else {
                alert('삭제 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('Error deleting mentorship:', error);
            alert('삭제 중 오류가 발생했습니다.');
        });
    }
}

// 페이지 로드 완료 후 이벤트 리스너 추가
document.addEventListener('DOMContentLoaded', function() {
    // 검색 입력 시 엔터키 처리
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMentorships();
            }
        });
    }
});