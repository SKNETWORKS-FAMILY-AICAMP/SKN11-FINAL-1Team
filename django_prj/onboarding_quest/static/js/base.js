// 온보딩 퀘스트 테마 색상 변수
window.tailwindTheme = {
  village: {
    sidebar: 'bg-gradient-to-b from-yellow-100 via-green-100 to-white',
    sidebarText: 'text-green-900',
    main: 'bg-gradient-to-br from-green-50 via-white to-yellow-50',
    button: 'bg-green-400 hover:bg-green-500 text-white',
    card: 'bg-white border border-yellow-200 shadow-xl',
    navHover: 'hover:bg-yellow-100',
  },
  dungeon: {
    sidebar: 'bg-gradient-to-b from-gray-900 via-gray-800 to-gray-700',
    sidebarText: 'text-purple-200',
    main: 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-700',
    button: 'bg-purple-700 hover:bg-purple-800 text-yellow-200',
    card: 'bg-gray-800 border border-purple-900 shadow-2xl',
    navHover: 'hover:bg-gray-800',
  }
};

// 사이드바 접기/펼치기
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');
const toggleIcon = document.getElementById('sidebarToggleIcon');
let sidebarOpen = true;
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
        // 접힌 상태: 햄버거(≡) 아이콘
        toggleIcon.innerHTML = `<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M3 6h18M3 12h18M3 18h18' />`;
    }
    document.querySelectorAll('#sidebar nav a').forEach(a => {
        a.style.display = sidebarOpen ? 'flex' : 'none';
    });
    document.querySelectorAll('.sidebar-text').forEach(e => {
        e.style.display = sidebarOpen ? 'inline-flex' : 'none';
    });
    document.getElementById('level-area').style.display = sidebarOpen ? 'block' : 'none';
});
document.querySelectorAll('#sidebar nav a').forEach(a => {
    a.style.display = 'flex';
});
// 테마 변경 기능
const themeSelect = document.getElementById('themeSelect');
function applyTheme(theme) {
    const t = window.tailwindTheme[theme];
    sidebar.className = `${t.sidebar} shadow-lg w-72 min-h-screen transition-all duration-300 ease-in-out flex flex-col`;
    document.body.className = `${t.main} min-h-screen flex transition-colors duration-300`;
    mainContent.className = `flex-1 flex flex-col transition-colors duration-300 ${t.main}`;
    document.querySelectorAll('.sidebar-link').forEach(a => {
        a.className = `sidebar-link block py-2 px-4 rounded ${t.navHover} ${t.sidebarText} flex items-center gap-2`;
    });
    document.querySelectorAll('.sidebar-text').forEach(e => {
        e.className = `font-extrabold text-2xl sidebar-text flex items-center gap-2 ${t.sidebarText}`;
    });
    // 레벨/경험치 Progress Bar 및 텍스트 색상도 테마에 맞게 조정
    if(theme === 'dungeon') {
        document.getElementById('level-area').className = 'px-6 py-4 border-b bg-gradient-to-r from-gray-900 to-gray-800';
        document.getElementById('userLevel').parentElement.className = 'text-lg font-bold text-purple-200 sidebar-text';
        document.getElementById('expBar').className = 'bg-gradient-to-r from-purple-700 to-yellow-400 h-4 rounded-full transition-all duration-500';
        document.getElementById('expBar').parentElement.className = 'w-full bg-gray-700 rounded-full h-4 mb-1';
        document.getElementById('userExp').parentElement.className = 'text-xs text-yellow-200 font-semibold sidebar-text';
        document.querySelector('#level-area .text-sm').className = 'text-sm text-yellow-200 bg-gray-800 px-2 py-1 rounded';
        document.getElementById('footer').className = 'bg-gradient-to-r from-gray-900 to-gray-800 text-center py-4 border-t shadow-xl';
        document.getElementById('footerText').className = 'text-yellow-200 font-semibold';
    } else {
        document.getElementById('level-area').className = 'px-6 py-4 border-b bg-gradient-to-r from-green-100 to-yellow-50';
        document.getElementById('userLevel').parentElement.className = 'text-lg font-bold text-green-800 sidebar-text';
        document.getElementById('expBar').className = 'bg-gradient-to-r from-green-400 to-yellow-400 h-4 rounded-full transition-all duration-500';
        document.getElementById('expBar').parentElement.className = 'w-full bg-yellow-100 rounded-full h-4 mb-1';
        document.getElementById('userExp').parentElement.className = 'text-xs text-green-700 font-semibold sidebar-text';
        document.querySelector('#level-area .text-sm').className = 'text-sm text-green-600 bg-green-100 px-2 py-1 rounded';
        document.getElementById('footer').className = 'bg-white text-center py-4 border-t';
        document.getElementById('footerText').className = 'text-green-400 font-semibold';
    }
}
themeSelect.addEventListener('change', e => {
    applyTheme(e.target.value);
    localStorage.setItem('theme', e.target.value);
});

// 페이지 로드 시 테마 적용
const savedTheme = localStorage.getItem('theme') || 'village';
themeSelect.value = savedTheme;
applyTheme(savedTheme);

// 기본 테마를 '마을 테마'로 설정
document.addEventListener('DOMContentLoaded', function() {
    var themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.value = 'village';
        // body에 마을 테마 클래스 적용 (예시: bg-village)
        document.body.classList.add('village-theme');
    }
});