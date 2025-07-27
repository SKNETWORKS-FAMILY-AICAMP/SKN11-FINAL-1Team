// ✅ doc.js (FastAPI 연동 + 기존 템플릿 구조 유지 + 누락 없이 완전 복원)

console.log("🔥 doc.js 로딩됨");

const dropArea = document.getElementById('doc-drop-area');
const fileInput = document.getElementById('doc-file-input');
let addedFiles = [];
const uploadListTbody = document.getElementById('doc-upload-list-tbody');
const uploadBtn = document.getElementById('doc-upload-btn');

let loadedDocuments = [];      // 전체 문서 목록 (최초 불러올 때 저장됨)
let filteredDocuments = [];    // 검색/필터 후 화면에 보여질 문서 목록

function renderUploadList() {
  if (!uploadListTbody) return;

  uploadListTbody.innerHTML = '';
  addedFiles.forEach((f, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
  <td style="width:5%;"></td> <!-- 체크박스 열 자리 맞춤 -->
  <td style="width:25%;">${f.name}</td>
  <td style="width:40%;">
    <input type="text" placeholder="설명 입력" value="${f.description}" 
           onchange="updateFileInfo(${idx}, 'description', this.value)">
  </td>
  <td style="width:15%; text-align: center;">
    <input type="checkbox" ${f.common_doc ? 'checked' : ''} 
           onchange="updateFileInfo(${idx}, 'common_doc', this.checked)">
  </td>
  <td style="width:15%; text-align: center;">
    <button class="remove-file-btn" onclick="removeFile(${idx})">❌</button>
  </td>
`;

    uploadListTbody.appendChild(tr);
  });

  const btnGroup = document.getElementById('doc-btn-group');
  const uploadBtn = document.getElementById('doc-upload-btn');
  const resetBtn = document.getElementById('doc-reset-btn');

  if (addedFiles.length > 0) {
    btnGroup?.classList.remove('hidden');
    uploadBtn?.classList.add('show');
    resetBtn?.classList.add('show');
  } else {
    btnGroup?.classList.add('hidden');
    uploadBtn?.classList.remove('show');
    resetBtn?.classList.remove('show');
  }

}

function applyFilters() {
  const search = document.getElementById("doc-search-input")?.value.toLowerCase() || "";
  const selectedDept = document.getElementById("department-filter")?.value;

  filteredDocuments = loadedDocuments.filter(doc => {
    const titleMatch = doc.title?.toLowerCase().includes(search);
    const descMatch = doc.description?.toLowerCase().includes(search);

    let deptMatch = true;
    if (selectedDept === "공통") {
      deptMatch = doc.common_doc === true;
    } else if (selectedDept) {
      deptMatch = doc.department?.department_name === selectedDept;
    }

    return (titleMatch || descMatch) && deptMatch;
  });

  renderDocTable(filteredDocuments);
}





function updateFileInfo(idx, field, value) {
  if (addedFiles[idx]) addedFiles[idx][field] = value;
}

function removeFile(idx) {
  addedFiles.splice(idx, 1);
  renderUploadList();
}

function isDuplicate(file) {
  return addedFiles.some(f =>
    f.file.name === file.name &&
    f.file.size === file.size &&
    f.file.lastModified === file.lastModified
  );
}

function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!isDuplicate(file)) {
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
  // fileInput.addEventListener('change', e => handleFiles(e.target.files));
  fileInput.addEventListener('change', e => {
    handleFiles(e.target.files);
    fileInput.value = '';  // 같은 파일을 다시 선택할 수 있도록 초기화
  });

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

      const response = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/docs/rag/upload`, {
        method: 'POST',
        body: formData
      });

      let result;
      try {
        result = await response.json();
      } catch (jsonError) {
        // JSON 파싱 실패 시 텍스트로 받아서 에러 표시
        const errorText = await response.text();
        throw new Error(`서버 응답 파싱 오류 (${response.status}): ${errorText}`);
      }

      if (!result.success) throw new Error(result.error || result.message || '업로드 실패');
    }

    showSuccess('모든 파일이 성공적으로 업로드되었습니다.');
    addedFiles = [];
    renderUploadList();
    // 토스트 메시지가 표시될 시간을 주고 페이지 새로고침
    setTimeout(() => {
      location.reload();
    }, 1500);

  } catch (err) {
    console.error('Upload error:', err);
    showError('업로드 실패: ' + err.message);
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
        showSuccess('수정되었습니다.');
        // 토스트 메시지가 표시될 시간을 주고 페이지 새로고침
        setTimeout(() => {
          location.reload();
        }, 1500);
      } else {
        showError('수정 실패: ' + data.error);
      }
    })
    .catch(err => {
      console.error('수정 오류:', err);
      showError('수정 중 오류가 발생했습니다.');
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

  const formData = new FormData();
  formData.append('docs_id', deleteDocId);
  formData.append('department_id', CURRENT_DEPARTMENT_ID);

  fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/docs/rag/${deleteDocId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${ACCESS_TOKEN}`
    }
  })
    .then(async res => {
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
        // JSON 파싱 실패 시 텍스트로 받아서 에러 표시
        const errorText = await res.text();
        throw new Error(`서버 응답 파싱 오류 (${res.status}): ${errorText}`);
      }
      return data;
    })
    .then(data => {
      if (data.success) {
        showSuccess('삭제되었습니다.');
        // 토스트 메시지가 표시될 시간을 주고 페이지 새로고침
        setTimeout(() => {
          location.reload();
        }, 1500);
      } else {
        showError('삭제 실패: ' + (data.error || data.message || '알 수 없는 오류'));
      }
    })
    .catch(err => {
      console.error('삭제 오류:', err);
      showError('삭제 중 오류가 발생했습니다: ' + err.message);
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
  try {
    const url = `${window.API_URLS.FASTAPI_BASE_URL}/api/docs/department/${departmentId}`;
    console.log("📡 요청 URL:", url);

    const response = await fetch(url);
    const data = await response.json();
    console.log("DOC LIST RESULT:", data);

    // 배열이 아니면 에러 출력
    if (!Array.isArray(data)) {
      const container = document.getElementById("doc-list");
      if (container) {
        container.innerHTML = `<tr><td colspan="5">문서 불러오기 실패: ${data.detail || '알 수 없는 오류'}</td></tr>`;
      }
      return;
    }

    // ✅ 데이터 저장하고 필터링 실행
    loadedDocuments = data;
    applyFilters();  // 🔍 검색어 + 부서 필터 적용 후 renderDocTable 실행됨

  } catch (error) {
    console.error("문서 목록 로드 오류:", error);
    const container = document.getElementById("doc-list");
    if (container) {
      container.innerHTML = `<tr><td colspan="5">문서 목록을 불러오는 중 오류가 발생했습니다.</td></tr>`;
    }
  }
}


function renderDocTable(docs) {
  const container = document.getElementById("doc-list");
  container.innerHTML = "";

  if (!Array.isArray(docs) || docs.length === 0) {
    container.innerHTML = `<tr><td colspan="5">검색된 문서가 없습니다.</td></tr>`;
    return;
  }

  docs.forEach(doc => {
    const tr = document.createElement("tr");
    tr.setAttribute("data-doc-id", doc.docs_id);

    const canEdit = doc.department_id === CURRENT_DEPARTMENT_ID;

    tr.innerHTML = `
      <td><input type="checkbox" class="doc-checkbox" data-doc-id="${doc.docs_id}"></td>
      <td>
        <a href="http://localhost:8001/api/docs/documents/download/${doc.docs_id}">
          📄 ${doc.title || "이름없음"}
          ${doc.common_doc ? '<span style="color:#38b2ac; font-weight:bold;"> [공통]</span>' : ''}
        </a>
      </td>
      <td>${doc.description || "-"}</td>
      <td style="text-align: center;">${doc.department ? doc.department.department_name : "-"}</td>
      <td style="text-align: center;">
        ${canEdit
        ? `<button class="doc-edit-btn" onclick="openEditModal(${doc.docs_id}, '${doc.description || ""}', ${doc.common_doc})">수정</button>
             <button class="doc-delete-btn" onclick="deleteDoc(${doc.docs_id})">삭제</button>`
        : `<span style="color:#999;">-</span>`}
      </td>
    `;
    container.appendChild(tr);
  });
}




function downloadDocument(docsId) {
  window.location.href = `${window.API_URLS.FASTAPI_BASE_URL}/api/documents/download/${docsId}`;
}


document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOM 로드 완료, CURRENT_DEPARTMENT_ID:", CURRENT_DEPARTMENT_ID);
  loadDocumentList(CURRENT_DEPARTMENT_ID);

  // 업로드 이벤트 등록
  document.getElementById("doc-search-input")?.addEventListener("input", applyFilters);
  document.getElementById("department-filter")?.addEventListener("change", applyFilters);
  document.getElementById("common-doc-toggle")?.addEventListener("change", applyFilters);


  document.body.addEventListener("dragover", preventDefaults, false);
  document.body.addEventListener("drop", handleDrop, false);

  document.addEventListener("change", function (e) {
    if (e.target.classList.contains("doc-checkbox") || e.target.id === "select-all-docs") {
      const checkboxes = document.querySelectorAll(".doc-checkbox");
      const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
      const btn = document.getElementById("bulk-delete-btn");
      if (btn) {
        btn.classList.toggle("show", anyChecked);

      }

      if (e.target.id === "select-all-docs") {
        checkboxes.forEach(cb => {
          cb.checked = e.target.checked;
          // ✅ 수동으로 change 이벤트를 발생시켜 버튼 갱신
          cb.dispatchEvent(new Event('change', { bubbles: true }));
        });
      }
    }
  });


  document.getElementById("bulk-delete-btn")?.addEventListener("click", async () => {
    const selected = [...document.querySelectorAll(".doc-checkbox:checked")];
    if (selected.length === 0) return;

    if (!(await showCustomConfirm(`${selected.length}개의 문서를 삭제하시겠습니까?`))) return;

    for (const cb of selected) {
      const docId = cb.dataset.docId;
      try {
        const res = await fetch(`${window.API_URLS.FASTAPI_BASE_URL}/api/docs/rag/${docId}`, { 
          method: "DELETE",
          headers: {
            'Authorization': `Bearer ${ACCESS_TOKEN}`
          }
        });
        const result = await res.json();
        if (!result.success) {
          console.warn("삭제 실패:", result.message);
        }
      } catch (err) {
        console.error("삭제 오류:", err);
      }
    }

    showSuccess("삭제가 완료되었습니다.");
    loadDocumentList(CURRENT_DEPARTMENT_ID);

    // ✅ 삭제 후 체크박스 초기화
    document.querySelectorAll(".doc-checkbox").forEach(cb => cb.checked = false);

    // ✅ 전체선택 체크박스 초기화
    const selectAll = document.getElementById("select-all-docs");
    if (selectAll) selectAll.checked = false;

    // ✅ 버튼 숨기기
    const btn = document.getElementById("bulk-delete-btn");
    if (btn) btn.classList.remove("show");
  });


  document.getElementById('doc-reset-btn')?.addEventListener('click', async () => {
    if (await showCustomConfirm("업로드 목록을 초기화하시겠습니까?")) {
      addedFiles = [];
      renderUploadList();
    }
  });

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

