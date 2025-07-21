// ✅ doc.js (FastAPI 연동 + 기존 템플릿 구조 유지 + 누락 없이 완전 복원)

console.log("🔥 doc.js 로딩됨");

const dropArea = document.getElementById('doc-drop-area');
const fileInput = document.getElementById('doc-file-input');
let addedFiles = [];
const uploadListTbody = document.getElementById('doc-upload-list-tbody');
const uploadBtn = document.getElementById('doc-upload-btn');

function renderUploadList() {
  if (!uploadListTbody) return;

  uploadListTbody.innerHTML = '';
  addedFiles.forEach((f, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="width:25%;">${f.name}</td>
      <td style="width:40%;"><input type="text" placeholder="설명 입력" value="${f.description}" onchange="updateFileInfo(${idx}, 'description', this.value)"></td>
      <td style="width:15%;"><input type="checkbox" ${f.common_doc ? 'checked' : ''} onchange="updateFileInfo(${idx}, 'common_doc', this.checked)"></td>
      <td style="width:20%;"><button class="remove-file-btn" onclick="removeFile(${idx})">제거</button></td>
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
  if (addedFiles[idx]) addedFiles[idx][field] = value;
}

function removeFile(idx) {
  addedFiles.splice(idx, 1);
  renderUploadList();
}

function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!addedFiles.some(f => f.name === file.name && f.size === file.size)) {
      addedFiles.push({ file, name: file.name, description: '', common_doc: false });
    }
  });
  renderUploadList();
}

if (dropArea && fileInput) {
  ['dragenter', 'dragover'].forEach(evt => {
    dropArea.addEventListener(evt, e => {
      e.preventDefault();
      dropArea.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    dropArea.addEventListener(evt, e => {
      e.preventDefault();
      dropArea.classList.remove('dragover');
    });
  });

  dropArea.addEventListener('drop', e => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  });

  dropArea.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', e => handleFiles(e.target.files));
}

uploadBtn?.addEventListener('click', async () => {
  if (addedFiles.length === 0) return;
  uploadBtn.disabled = true;
  uploadBtn.textContent = '업로드 중...';

  try {
    for (const fileInfo of addedFiles) {
      const formData = new FormData();
      formData.append('file', fileInfo.file);
      formData.append('title', fileInfo.name);  // ✅ FastAPI → Django 업로드에서 필요
      formData.append('description', fileInfo.description);
      formData.append('common_doc', fileInfo.common_doc ? 'true' : 'false');
      formData.append('department_id', CURRENT_DEPARTMENT_ID);
      formData.append('original_file_name', fileInfo.name);

      const response = await fetch('http://localhost:8001/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (!result.success) throw new Error(result.error || '업로드 실패');
    }

    alert('모든 파일이 성공적으로 업로드되었습니다.');
    addedFiles = [];
    renderUploadList();
    location.reload();

  } catch (err) {
    console.error('Upload error:', err);
    alert('업로드 실패: ' + err.message);
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = '📤 업로드';
  }
});
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

document.getElementById('edit-form')?.addEventListener('submit', function (e) {
  e.preventDefault();
  const docId = this.dataset.docId;
  const description = document.getElementById('edit-description').value;
  const commonDocChecked = document.getElementById('edit-common-doc').checked;

  const formData = new FormData();
  formData.append('description', description);
  formData.append('common_doc', commonDocChecked ? 'true' : 'false');
  formData.append('docs_id', docId);
  formData.append('department_id', CURRENT_DEPARTMENT_ID);

  fetch(`/common/doc/${docId}/update/`, {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert('수정되었습니다.');
        location.reload();
      } else {
        alert('수정 실패: ' + data.error);
      }
    })
    .catch(err => {
      console.error('수정 오류:', err);
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

// function confirmDelete() {
//   if (!deleteDocId) return;

//   const formData = new FormData();
//   formData.append('docs_id', deleteDocId);
//   formData.append('department_id', CURRENT_DEPARTMENT_ID);

//   fetch(`/common/doc/${deleteDocId}/delete/`, {
//     method: 'POST',
//     body: formData
//   })
//     .then(res => res.json())
//     .then(data => {
//       if (data.success) {
//         alert('삭제되었습니다.');
//         location.reload();
//       } else {
//         alert('삭제 실패: ' + data.error);
//       }
//     })
//     .catch(err => {
//       console.error('삭제 오류:', err);
//       alert('삭제 중 오류가 발생했습니다.');
//     });

//   closeDeleteModal();
// }


function confirmDelete() {
  if (!deleteDocId) return;

  const formData = new FormData();
  formData.append('docs_id', deleteDocId);
  formData.append('department_id', CURRENT_DEPARTMENT_ID);

  fetch('http://localhost:8001/delete', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert('삭제되었습니다.');
        location.reload();
      } else {
        alert('삭제 실패: ' + data.error);
      }
    })
    .catch(err => {
      console.error('삭제 오류:', err);
      alert('삭제 중 오류가 발생했습니다.');
    });

  closeDeleteModal();
}



//#endregion

// 외부 클릭 시 모달 닫기
window.addEventListener('click', function (e) {
  if (e.target === document.getElementById('edit-modal')) closeEditModal();
  if (e.target === document.getElementById('deleteModal')) closeDeleteModal();
});

async function loadDocumentList(departmentId) {
  const response = await fetch(`http://localhost:8001/list?department_id=${departmentId}`);
  const data = await response.json();
  console.log("DOC LIST RESULT:", data);

  const container = document.getElementById("doc-list");
  if (!container) return;

  container.innerHTML = "";

  if (!data.success) {
    container.innerHTML = `<tr><td colspan="4">문서 불러오기 실패: ${data.error}</td></tr>`;
    return;
  }

  data.docs.forEach(doc => {
    const tr = document.createElement("tr");
    tr.setAttribute("data-doc-id", doc.docs_id);

    const canEdit = doc.department_id === CURRENT_DEPARTMENT_ID;

    tr.innerHTML = `
    <td>
      <a href="http://localhost:8001/download/${doc.docs_id}" target="_blank">
        📄 ${doc.title || "이름없음"}

      </a>
    </td>
    <td>${doc.description || "-"}</td>
    <td>${doc.department_name || "-"}</td>
    <td>
      ${canEdit
        ? `
          <button class="doc-edit-btn" onclick="openEditModal(${doc.docs_id}, '${doc.description || ""}', ${doc.common_doc})">수정</button>
          <button class="doc-delete-btn" onclick="deleteDoc(${doc.docs_id})">삭제</button>
        `
        : `<span style="color:#999;">-</span>`
      }
    </td>
  `;
    container.appendChild(tr);
  });
}



function downloadDocument(docsId) {
  window.location.href = `http://localhost:8001/download/${docsId}`;
}


document.addEventListener("DOMContentLoaded", () => {
  loadDocumentList(CURRENT_DEPARTMENT_ID);

  // 업로드 이벤트 등록
  document.body.addEventListener("dragover", preventDefaults, false);
  document.body.addEventListener("drop", handleDrop, false);
});


function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDrop(e) {
  preventDefaults(e);
  const dt = e.dataTransfer;
  const files = dt.files;
  handleUpload(files);
}

function handleUpload(files) {
  if (!files || files.length === 0) return;
  Array.from(files).forEach(file => {
    if (!addedFiles.some(f => f.name === file.name && f.size === file.size)) {
      addedFiles.push({ file, name: file.name, description: '', common_doc: false });
    }
  });
  renderUploadList();
}

