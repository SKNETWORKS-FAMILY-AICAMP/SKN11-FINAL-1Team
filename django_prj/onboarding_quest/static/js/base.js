const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');
const toggleIcon = document.getElementById('sidebarToggleIcon');
let sidebarOpen = true;

if (toggleBtn && sidebar && mainContent && toggleIcon) {
    toggleBtn.addEventListener('click', () => {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            // 사이드바 펼치기
            sidebar.style.width = '18rem';
            sidebar.classList.remove('sidebar-collapsed');
            mainContent.style.marginLeft = '18rem';
            // 펼쳐진 상태: 햄버거 메뉴 아이콘
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 6h16M4 12h16M4 18h16' />`;
        } else {
            // 사이드바 접기
            sidebar.style.width = '4rem';
            sidebar.classList.add('sidebar-collapsed');
            mainContent.style.marginLeft = '4rem';
            // 접힌 상태: 화살표 아이콘 (펼치기)
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 5l7 7-7 7' />`;
        }
    });
}