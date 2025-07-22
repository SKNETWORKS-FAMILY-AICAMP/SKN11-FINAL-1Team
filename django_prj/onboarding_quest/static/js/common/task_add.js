
const levelBtns = document.querySelectorAll('.level-btn');
const levelInput = document.getElementById('level-input');
levelBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        levelBtns.forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        levelInput.value = this.dataset.level;
    });
});
