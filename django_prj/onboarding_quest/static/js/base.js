const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');
const toggleIcon = document.getElementById('sidebarToggleIcon');
let sidebarOpen = true;
if (toggleBtn && sidebar && mainContent && toggleIcon) {
    toggleBtn.addEventListener('click', () => {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            sidebar.style.width = '18rem';
            mainContent.classList.remove('ml-0');
            // 펼쳐진 상태: 닫기(←) 아이콘
            toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 6h16M4 12h16M4 18h16' />`;
        } else {
            sidebar.style.width = '4rem';
            mainContent.classList.add('ml-0');
            var footerText = document.getElementById('footerText');
            if (footerText) footerText.className = 'text-green-400 font-semibold';
        }
    });
}