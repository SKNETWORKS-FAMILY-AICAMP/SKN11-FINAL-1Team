/**
 * 커리큘럼 관리 페이지 JavaScript
 */
class CurriculumManager {
    constructor() {
        this.items = document.querySelectorAll('.template-item');
        this.detailDiv = document.getElementById('curriculum-detail');
        this.curriculumTasks = window.curriculumTasksData || {};
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.renderFirstCurriculum();
    }

    bindEvents() {
        // 커리큘럼 목록 클릭 이벤트
        this.items.forEach(item => {
            item.addEventListener('click', () => this.selectCurriculum(item));
        });

        // 버튼 클릭 이벤트
        this.bindButtonEvents();
    }

    bindButtonEvents() {
        // 커리큘럼 생성 버튼
        const addBtn = document.querySelector('.add-template-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                window.location.href = '/mentor/add_template/';
            });
        }

        // 상세 페이지 버튼들에 직접 이벤트 리스너 등록
        const cloneBtn = document.querySelector('#clone-btn');
        const deleteBtn = document.querySelector('#delete-btn');
        const editBtn = document.querySelector('#edit-btn');
        
        if (cloneBtn) {
            cloneBtn.addEventListener('click', () => this.handleDetailButtonClick(cloneBtn));
        }
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.handleDetailButtonClick(deleteBtn));
        }
        if (editBtn) {
            editBtn.addEventListener('click', () => this.handleDetailButtonClick(editBtn));
        }
    }

    async handleDetailButtonClick(button) {
        const buttonId = button.id;
        const selectedItem = document.querySelector('.template-item.selected');
        if (!selectedItem) return;
        
        const curriculumId = selectedItem.getAttribute('data-id');
        const isCommon = selectedItem.getAttribute('data-common') === 'True';
        
        if (buttonId === 'clone-btn') {
            // AJAX POST로 복제 요청
            fetch(`/mentor/api/clone_curriculum/${curriculumId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccess('복제 완료!');
                    // 토스트 메시지가 표시될 시간을 주고 페이지 새로고침
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showError(data.message || '복제 실패');
                }
            })
            .catch(() => showError('복제 중 오류 발생'));
            return;
        }
        
        if (isCommon && (buttonId === 'delete-btn' || buttonId === 'edit-btn')) {
            showWarning('공용 커리큘럼은 수정/삭제할 수 없습니다.');
            return;
        }
        
        if (buttonId === 'delete-btn') {
            if (!(await showCustomConfirm('정말로 이 커리큘럼을 삭제하시겠습니까?'))) return;
            fetch(`/mentor/api/delete_curriculum/${curriculumId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccess('삭제 완료!');
                    // 토스트 메시지가 표시될 시간을 주고 페이지 새로고침
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showError(data.message || '삭제 실패');
                }
            })
            .catch(() => showError('삭제 중 오류 발생'));
            return;
        }
        
        if (buttonId === 'edit-btn') {
            window.location.href = `/mentor/add_template/${curriculumId}/`;
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
        
        // DOM을 직접 생성하여 textContent 사용
        this.detailDiv.innerHTML = '';
        
        // 공용 커리큘럼 섹션
        const commonSection = document.createElement('div');
        commonSection.className = 'template-detail-section';
        commonSection.innerHTML = `
            <div class="template-detail-title">공용 커리큘럼 여부</div>
            <label class="checkbox-container">
                <input type="checkbox" ${data.common ? 'checked' : ''} disabled>
                공용 커리큘럼
            </label>
        `;
        this.detailDiv.appendChild(commonSection);
        
        // 제목 섹션
        const titleSection = document.createElement('div');
        titleSection.className = 'template-detail-section';
        titleSection.innerHTML = '<div class="template-detail-title">커리큘럼 제목</div>';
        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.className = 'template-detail-input';
        titleInput.value = data.title || '';
        titleInput.readOnly = true;
        titleSection.appendChild(titleInput);
        this.detailDiv.appendChild(titleSection);
        
        // 설명 섹션
        const descSection = document.createElement('div');
        descSection.className = 'template-detail-section';
        descSection.innerHTML = '<div class="template-detail-title">커리큘럼 설명</div>';
        const descTextarea = document.createElement('textarea');
        descTextarea.className = 'template-detail-textarea';
        descTextarea.readOnly = true;
        descTextarea.textContent = data.desc || '';
        descSection.appendChild(descTextarea);
        this.detailDiv.appendChild(descSection);
        
        // 주차 섹션
        const weeksSection = document.createElement('div');
        weeksSection.className = 'template-detail-section';
        weeksSection.innerHTML = '<div class="template-detail-title">주차별 온보딩 일정</div>';
        const weeksTextarea = document.createElement('textarea');
        weeksTextarea.className = 'template-detail-textarea';
        weeksTextarea.readOnly = true;
        weeksTextarea.textContent = data.weeks || '';
        weeksSection.appendChild(weeksTextarea);
        this.detailDiv.appendChild(weeksSection);
        
        // 태스크 섹션
        const taskSection = document.createElement('div');
        taskSection.className = 'template-detail-section';
        taskSection.innerHTML = `
            <div class="template-detail-title">세부 Task</div>
            <div class="template-task-list">
                ${this.buildTaskList(tasks)}
            </div>
        `;
        this.detailDiv.appendChild(taskSection);

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
            title: this.unescapeString(item.getAttribute('data-title')),
            desc: this.unescapeString(item.getAttribute('data-desc')),
            weeks: this.processWeeksData(this.unescapeString(item.getAttribute('data-weeks')))
        };
    }

    // 유니코드 이스케이프 문자를 실제 문자로 변환
    unescapeString(str) {
        if (!str) return str;
        // 모든 \uXXXX를 실제 문자로 변환
        return str.replace(/\\u([\dA-Fa-f]{4})/g, function(match, grp) {
            return String.fromCharCode(parseInt(grp, 16));
        });
    }

    processWeeksData(weeksData) {
        if (!weeksData) return '';
        // 이미 unescapeString에서 유니코드 처리됨
        return weeksData
            .replace(/\\n/g, '\n') // 이스케이프된 \n
            .replace(/\r\n|\r|\n/g, '\n') // 실제 줄바꿈 문자
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<[^>]*>/g, '')
            .replace(/&lt;br&gt;/gi, '\n')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#x27;/g, "'");
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
                // 태스크의 텍스트도 유니코드 이스케이프 처리
                const title = this.unescapeString(task.title || '');
                const guideline = this.unescapeString(task.guideline || '-');
                const description = this.unescapeString(task.description || '-');
                const period = this.unescapeString(task.period || '-');
                const priority = this.unescapeString(task.priority || '-');
                
                html += `
                <div class="task-card">
                    <div class="task-card-title">${title}</div>
                    <div class="task-card-row"><span class="task-card-label">가이드라인</span> <span class="task-card-value">${guideline}</span></div>
                    <div class="task-card-row"><span class="task-card-label">설명</span> <span class="task-card-value">${description}</span></div>
                    <div class="task-card-row"><span class="task-card-label">과제기간</span> <span class="task-card-value">${period}</span></div>
                    <div class="task-card-row"><span class="task-card-label">우선순위</span> <span class="task-card-value">${priority}</span></div>
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
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }
}

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    new CurriculumManager();
});
