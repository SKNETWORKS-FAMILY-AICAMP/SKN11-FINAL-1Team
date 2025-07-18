//#region 문서 업로드
const dropArea = document.getElementById('doc-drop-area');
const fileInput = document.getElementById('doc-file-input');

if (dropArea && fileInput) {
  ['dragenter', 'dragover'].forEach(evt => dropArea.addEventListener(evt, e => {
    e.preventDefault();
    dropArea.classList.add('dragover');
  }));

  ['dragleave', 'drop'].forEach(evt => dropArea.addEventListener(evt, e => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
  }));

  dropArea.addEventListener('drop', e => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  });

  dropArea.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', e => handleFiles(e.target.files));
}

let addedFiles = [];
const uploadListTbody = document.getElementById('doc-upload-list-tbody');
const uploadBtn = document.getElementById('doc-upload-btn');

function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!addedFiles.some(f => f.name === file.name && f.size === file.size)) {
      addedFiles.push({
        file,
        name: file.name,
        description: '',
        tags: '',
        common_doc: false
      });
    }
  });
  renderUploadList();
}

function renderUploadList() {
  if (!uploadListTbody) return;

  uploadListTbody.innerHTML = '';
  addedFiles.forEach((f, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
            <td>${f.name}</td>
            <td><input type="text" value="${f.description}" onchange="updateFileInfo(${idx}, 'description', this.value)"></td>
            <td><input type="text" value="${f.tags}" onchange="updateFileInfo(${idx}, 'tags', this.value)"></td>
            <td><input type="checkbox" ${f.common_doc ? 'checked' : ''} onchange="updateFileInfo(${idx}, 'common_doc', this.checked)"></td>
            <td><button class="remove-file-btn" onclick="removeFile(${idx})">제거</button></td>
        `;
    uploadListTbody.appendChild(tr);
  });

  if (uploadBtn) {
    if (addedFiles.length > 0) {
      uploadBtn.classList.add('show');
    } else {
      uploadBtn.classList.remove('show');
    }
  }
}

function updateFileInfo(idx, field, value) {
  if (addedFiles[idx]) {
    addedFiles[idx][field] = value;
  }
}

function removeFile(idx) {
  addedFiles.splice(idx, 1);
  renderUploadList();
}

// 업로드 버튼 클릭 시 실행
if (uploadBtn) {
  uploadBtn.addEventListener('click', async () => {
    if (addedFiles.length === 0) return;

    try {
      for (const fileInfo of addedFiles) {
        const formData = new FormData();
        formData.append('file', fileInfo.file);
        formData.append('title', fileInfo.name);
        formData.append('description', fileInfo.description);
        formData.append('tags', fileInfo.tags);
        formData.append('common_doc', fileInfo.common_doc);

        const response = await fetch('/common/doc/upload/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken()
          },
          body: formData
        });

        const result = await response.json();
        if (!result.success) {
          alert(`업로드 실패: ${result.error}`);
          return;
        }
      }

      alert('모든 파일이 성공적으로 업로드되었습니다.');
      addedFiles = [];
      renderUploadList();
      window.location.reload();

    } catch (error) {
      console.error('업로드 오류:', error);
      alert('업로드 중 오류가 발생했습니다.');
    }
  });
}

//#region 파일 다운로드 처리
// 다운로드 링크 클릭 시 추가 처리
document.addEventListener('DOMContentLoaded', function () {
  const downloadLinks = document.querySelectorAll('.doc-download-link');

  downloadLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault(); // 기본 동작 방지

      const fileName = this.textContent.trim();
      const downloadUrl = this.href;

      // 다운로드 시작 알림
      console.log(`파일 다운로드 시작: ${fileName}`);

      // 새 창에서 다운로드 시작
      const downloadWindow = window.open(downloadUrl, '_blank');

      // 즉시 창 닫기 (다운로드만 시작)
      setTimeout(() => {
        if (downloadWindow) {
          downloadWindow.close();
        }
      }, 100);

      // 다운로드 버튼 임시 비활성화
      this.style.pointerEvents = 'none';
      this.style.opacity = '0.7';

      // 3초 후 다시 활성화
      setTimeout(() => {
        this.style.pointerEvents = 'auto';
        this.style.opacity = '1';
      }, 3000);
    });
  });
});


// 파일 다운로드 함수
function downloadFile(docId) {
  // 다운로드 링크 생성
  const downloadLink = document.createElement('a');
  downloadLink.href = `/common/doc/${docId}/download/`;
  downloadLink.download = '';
  downloadLink.style.display = 'none';

  // 임시로 DOM에 추가
  document.body.appendChild(downloadLink);

  // 클릭하여 다운로드 시작
  downloadLink.click();

  // DOM에서 제거
  document.body.removeChild(downloadLink);
}

//#region 문서 관리 기능
let currentDocId = null;

function editDoc(docId) {
  console.log('수정 기능 - 문서 ID:', docId);
  alert('수정 기능은 추후 구현 예정입니다.');
}

function deleteDoc(docId) {
  currentDocId = docId;
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.style.display = 'flex';
  } else {
    if (confirm('정말로 이 문서를 삭제하시겠습니까?')) {
      performDelete(docId);
    }
  }
}

function confirmDelete() {
  if (currentDocId) {
    performDelete(currentDocId);
    closeDeleteModal();
  }
}

function performDelete(docId) {
  fetch(`/common/doc/${docId}/delete/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('문서가 성공적으로 삭제되었습니다.');
        const row = document.querySelector(`tr[data-doc-id="${docId}"]`);
        if (row) {
          row.remove();
        }
        window.location.reload();
      } else {
        alert('삭제 실패: ' + (data.error || '알 수 없는 오류'));
      }
    })
    .catch(error => {
      console.error('삭제 요청 오류:', error);
      alert('삭제 중 오류가 발생했습니다.');
    });
}

function closeDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.style.display = 'none';
  }
  currentDocId = null;
}

function getCsrfToken() {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
  return csrfToken ? csrfToken.value : '';
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeDeleteModal();
  }
});
//#endregion
