//#region 문서 업로드
const dropArea = document.getElementById('doc-drop-area');
const fileInput = document.getElementById('doc-file-input');

if (dropArea && fileInput) {
  ['dragenter', 'dragover'].forEach(evt =>
    dropArea.addEventListener(evt, e => {
      e.preventDefault();
      dropArea.classList.add('dragover');
    })
  );

  ['dragleave', 'drop'].forEach(evt =>
    dropArea.addEventListener(evt, e => {
      e.preventDefault();
      dropArea.classList.remove('dragover');
    })
  );

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
            <td><input type="text" placeholder="설명 입력" value="${f.description}" onchange="updateFileInfo(${idx}, 'description', this.value)"></td>
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

if (uploadBtn) {
  uploadBtn.addEventListener('click', async () => {
    if (addedFiles.length === 0) return;

    uploadBtn.disabled = true;
    uploadBtn.textContent = '업로드 중...';

    try {
      for (const fileInfo of addedFiles) {
        const formData = new FormData();
        formData.append('file', fileInfo.file);
        formData.append('title', fileInfo.name);
        formData.append('description', fileInfo.description);
        formData.append('tags', fileInfo.tags);
        formData.append('common_doc', fileInfo.common_doc ? 'true' : 'false');

        const response = await fetch('/common/doc/upload/', {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          }
        });

        const result = await response.json();
        if (!result.success) {
          throw new Error(result.error || '업로드 실패');
        }
      }

      alert('모든 파일이 성공적으로 업로드되었습니다.');
      addedFiles = [];
      renderUploadList();
      location.reload();

    } catch (error) {
      console.error('Upload error:', error);
      alert('업로드 중 오류가 발생했습니다: ' + error.message);
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.textContent = '📤 업로드';
    }
  });
}
//#endregion

//#region 문서 수정 기능
function openEditModal(docId, currentDescription, currentCommonDoc) {
  document.getElementById('edit-description').value = currentDescription || '';
  
  document.getElementById('edit-common-doc').checked = currentCommonDoc === true || currentCommonDoc === 'true';
  document.getElementById('edit-modal').style.display = 'flex';
  document.getElementById('edit-form').dataset.docId = docId;
}



function closeEditModal() {
  document.getElementById('edit-modal').style.display = 'none';
}

// 수정 폼 제출
document.getElementById('edit-form').addEventListener('submit', function (e) {
  e.preventDefault();

  const docId = this.dataset.docId;
  const description = document.getElementById('edit-description').value;
  
  const commonDocChecked = document.getElementById('edit-common-doc').checked;

  const formData = new FormData();
  formData.append('description', description);
  
  formData.append('common_doc', commonDocChecked ? 'true' : 'false');  // ← 문자열로 명확하게 전달

  fetch(`/common/doc/${docId}/update/`, {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('수정되었습니다.');
        location.reload();
      } else {
        alert('오류: ' + data.error);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('수정 중 오류가 발생했습니다.');
    });

  closeEditModal();
});
//#endregion

//#region 문서 삭제 기능
let deleteDocId = null;

function deleteDoc(docId) {
  deleteDocId = docId;
  document.getElementById('deleteModal').style.display = 'flex';
}

function closeDeleteModal() {
  document.getElementById('deleteModal').style.display = 'none';
  deleteDocId = null;
}

function confirmDelete() {
  if (!deleteDocId) return;

  fetch(`/common/doc/${deleteDocId}/delete/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('문서가 삭제되었습니다.');
        location.reload();
      } else {
        alert('삭제 중 오류가 발생했습니다: ' + data.error);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('삭제 중 오류가 발생했습니다.');
    });

  closeDeleteModal();
}
//#endregion

// 모달 외부 클릭 시 닫기
window.addEventListener('click', function (e) {
  const editModal = document.getElementById('edit-modal');
  const deleteModal = document.getElementById('deleteModal');

  if (e.target === editModal) {
    closeEditModal();
  }
  if (e.target === deleteModal) {
    closeDeleteModal();
  }
});
