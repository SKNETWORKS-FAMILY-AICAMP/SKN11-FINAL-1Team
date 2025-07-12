//#region 문서 업로드
// 드래그&드롭, 파일 선택, 업로드 버튼 등 업로드 관련 기능
const dropArea = document.getElementById('doc-drop-area');
const fileInput = document.getElementById('doc-file-input');
['dragenter','dragover'].forEach(evt => dropArea.addEventListener(evt, e => {
  e.preventDefault(); dropArea.classList.add('dragover');
}));
['dragleave','drop'].forEach(evt => dropArea.addEventListener(evt, e => {
  e.preventDefault(); dropArea.classList.remove('dragover');
}));
dropArea.addEventListener('drop', e => {
  e.preventDefault(); handleFiles(e.dataTransfer.files);
});
dropArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => handleFiles(e.target.files));
//#endregion



//#region 추가된 파일
// 업로드 전 추가된 파일 목록 관리 및 렌더링
let addedFiles = [];
const uploadListTbody = document.getElementById('doc-upload-list-tbody');
const uploadBtn = document.getElementById('doc-upload-btn');

function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!addedFiles.some(f => f.name === file.name && f.size === file.size)) {
      addedFiles.push({ file, name: file.name, description: '', tags: '', common_doc: false });
    }
  });
  renderUploadList();
}

function renderUploadList() {
  uploadListTbody.innerHTML = '';
  addedFiles.forEach((f, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text" value="${f.name}" onchange="addedFiles[${idx}].name=this.value"></td>
      <td><input type="text" value="${f.description||''}" onchange="addedFiles[${idx}].description=this.value"></td>
      <td><input type="text" class="doc-tag-input" value="${f.tags||''}" onchange="addedFiles[${idx}].tags=this.value" placeholder="쉼표로 구분"></td>
      <td><input type="checkbox" ${f.common_doc ? 'checked' : ''} onchange="addedFiles[${idx}].common_doc=this.checked"></td>
    `;
    uploadListTbody.appendChild(tr);
  });
}

uploadBtn.addEventListener('click', function() {
  if (!addedFiles.length) return alert('업로드할 파일을 추가하세요.');
  addedFiles.forEach(f => {
    fetch('/common/doc/upload/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        name: f.name,
        description: f.description,
        tags: f.tags,
        common_doc: !!f.common_doc
      })
    })
    .then(res => res.json())
    .then(data => {
      if (!data.success) alert('업로드 실패: ' + (data.error || ''));
      else location.reload();
    });
  });
  addedFiles = [];
  renderUploadList();
});
//#endregion



//#region 3. 등록된 파일 목록
// 등록된 파일 목록(수정/삭제)은 서버 렌더링 및 별도 ajax로 관리됨 (이 파일에서는 직접 관리하지 않음)

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

// 최초 렌더링
renderUploadList();
//#endregion
