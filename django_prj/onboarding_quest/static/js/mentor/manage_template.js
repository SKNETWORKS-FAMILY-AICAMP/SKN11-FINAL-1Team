// 템플릿 선택 시 상세 페이지 이동
const items = document.querySelectorAll('.template-item');
items.forEach(item => {
    item.addEventListener('click', () => {
        const templateId = item.getAttribute('data-id');
        if (templateId) {
            window.location.href = `/template/detail/${templateId}/`;
        }
    });
});