// 삭제 버튼 클릭 시 확인창 (추후 확장 가능)
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a[title="삭제"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if(!confirm('정말 삭제하시겠습니까?')) {
                e.preventDefault();
            }
        });
    });
});
