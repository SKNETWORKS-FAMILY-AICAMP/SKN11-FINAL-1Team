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
            // effective_is_active 값을 사용하여 실제 활성 상태 표시
            document.getElementById('edit-status').value = data.effective_is_active ? 'true' : 'false';
            
            console.log('Setting modal status to:', data.effective_is_active, '(effective_is_active)');
            console.log('Raw mentorship is_active:', data.is_active);
            
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
            alert('멘토쉽이 성공적으로 수정되었습니다.');
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