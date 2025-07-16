// 커리큘럼 선택 시 상세 페이지 이동
const items = document.querySelectorAll('.template-item');
items.forEach(item => {
    item.addEventListener('click', () => {
        const templateId = item.getAttribute('data-id');
        if (templateId) {
            window.location.href = `/template/detail/${templateId}/`;
        }
<<<<<<< Updated upstream
    });
});
=======

        // 상세 페이지 버튼들
        const buttons = document.querySelectorAll('.template-detail-header .template-btn, .template-detail-header .template-edit-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => this.handleDetailButtonClick(button));
        });
    }

    handleDetailButtonClick(button) {
        const action = button.textContent.trim();
        const selectedItem = document.querySelector('.template-item.selected');
        if (!selectedItem) return;
        const curriculumId = selectedItem.getAttribute('data-id');
        const isCommon = selectedItem.getAttribute('data-common') === 'True';
        if (action === '복제') {
            // AJAX POST로 복제 요청
            fetch(`/mentor/clone_template/${curriculumId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('복제 완료!');
                    window.location.reload();
                } else {
                    alert(data.message || '복제 실패');
                }
            })
            .catch(() => alert('복제 중 오류 발생'));
            return;
        }
        if (isCommon) return; // 공용은 삭제/편집 불가
        if (action === '삭제') {
            if (!confirm('정말로 이 커리큘럼을 삭제하시겠습니까?')) return;
            fetch(`/mentor/delete_template/${curriculumId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('삭제 완료!');
                    window.location.reload();
                } else {
                    alert(data.message || '삭제 실패');
                }
            })
            .catch(() => alert('삭제 중 오류 발생'));
            return;
        }
        if (action === '커리큘럼 편집') {
            window.location.href = `/mentor/edit_template/${curriculumId}/`;
        }
    }

    selectCurriculum(item) {
        // 선택 상태 변경
        this.items.forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');
        
        // 상세 정보 렌더링
        this.renderCurriculumDetail(item);
    }

    renderCurriculumDetail(item) {
        const data = this.extractCurriculumData(item);
        const tasks = this.curriculumTasks[data.id] || [];
        const html = this.buildDetailHTML(data, tasks);
        this.detailDiv.innerHTML = html;

        // 공용 커리큘럼이면 삭제/편집 버튼 숨김
        const isCommon = data.common;
        const delBtn = document.querySelector('.template-detail-header .template-btn:nth-child(2)');
        const editBtn = document.querySelector('.template-detail-header .template-edit-btn');
        if (delBtn) delBtn.style.display = isCommon ? 'none' : '';
        if (editBtn) editBtn.style.display = isCommon ? 'none' : '';
    }

    extractCurriculumData(item) {
        return {
            id: item.getAttribute('data-id'),
            common: item.getAttribute('data-common') === 'True',
            title: item.getAttribute('data-title'),
            desc: item.getAttribute('data-desc'),
            weeks: this.processWeeksData(item.getAttribute('data-weeks'))
        };
    }

    processWeeksData(weeksData) {
        if (!weeksData) return '';
        // \n, \r\n, <br>, \u000A 등 모두 줄바꿈으로 변환
        return weeksData
            .replace(/\\u000a/gi, '\n') // 유니코드 이스케이프 줄바꿈
            .replace(/\\n/g, '\n') // 이스케이프된 \n
            .replace(/\r\n|\r|\n/g, '\n') // 실제 줄바꿈 문자
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<[^>]*>/g, '')
            .replace(/&lt;br&gt;/gi, '\n')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#x27;/g, "'")
            .split('\n').join('\n'); // textarea에서 줄바꿈 표시
    }

    buildDetailHTML(data, tasks) {
        return `
            <div class="template-detail-section">
                <div class="template-detail-title">공용 커리큘럼 여부</div>
                <label class="checkbox-container">
                    <input type="checkbox" ${data.common ? 'checked' : ''} disabled>
                    공용 커리큘럼
                </label>
            </div>
            
            <div class="template-detail-section">
                <div class="template-detail-title">커리큘럼 제목</div>
                <input type="text" class="template-detail-input" value="${data.title}" readonly>
            </div>
            
            <div class="template-detail-section">
                <div class="template-detail-title">커리큘럼 설명</div>
                <textarea class="template-detail-textarea" readonly>${data.desc || ''}</textarea>
            </div>
            
            <div class="template-detail-section">
                <div class="template-detail-title">주차별 온보딩 일정</div>
                <textarea class="template-detail-textarea" readonly>${data.weeks.replace(/\n/g, '\r\n')}</textarea>
            </div>
            
            <div class="template-detail-section">
                <div class="template-detail-title">세부 Task</div>
                <div class="template-task-list">
                    ${this.buildTaskList(tasks)}
                </div>
            </div>
        `;
    }

    buildTaskList(tasks) {
        if (!tasks || tasks.length === 0) {
            return '<div class="no-tasks">세부 Task가 없습니다.</div>';
        }
        // 주차별로 그룹핑
        const weekMap = {};
        tasks.forEach(task => {
            const week = task.week || 0;
            if (!weekMap[week]) weekMap[week] = [];
            weekMap[week].push(task);
        });
        // 주차 오름차순 정렬
        const sortedWeeks = Object.keys(weekMap).sort((a, b) => a - b);
        let html = '';
        sortedWeeks.forEach(week => {
            html += `<div class="task-week-group"><div class="task-week-title">${week}주차</div>`;
            weekMap[week].forEach(task => {
                html += `
                <div class="task-card">
                    <div class="task-card-title">${task.title || ''}</div>
                    <div class="task-card-row"><span class="task-card-label">가이드라인</span> <span class="task-card-value">${task.guideline || '-'}</span></div>
                    <div class="task-card-row"><span class="task-card-label">설명</span> <span class="task-card-value">${task.description || '-'}</span></div>
                    <div class="task-card-row"><span class="task-card-label">과제기간</span> <span class="task-card-value">${task.period || '-'}</span></div>
                    <div class="task-card-row"><span class="task-card-label">우선순위</span> <span class="task-card-value">${task.priority || '-'}</span></div>
                </div>
                `;
            });
            html += '</div>';
        });
        return html;
    }

    renderFirstCurriculum() {
        const firstSelected = document.querySelector('.template-item.selected');
        if (firstSelected) {
            this.renderCurriculumDetail(firstSelected);
        }
    }

    getCSRFToken() {
        // 여러 소스에서 CSRF 토큰을 찾아서 반환
        let token = null;
        
        // 1. 쿠키에서 찾기
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                token = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            }
        }
        
        // 2. 메타 태그에서 찾기
        if (!token) {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) {
                token = metaTag.getAttribute('content');
            }
        }
        
        // 3. 폼의 hidden input에서 찾기
        if (!token) {
            const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (hiddenInput) {
                token = hiddenInput.value;
            }
        }
        
        return token || '';
    }
}

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    new CurriculumManager();
});
>>>>>>> Stashed changes
