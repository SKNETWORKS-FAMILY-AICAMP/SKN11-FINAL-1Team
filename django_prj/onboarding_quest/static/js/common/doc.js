function showCategory(cat) {
    document.getElementById('cat1-list').style.display = 'none';
    document.getElementById('cat2-list').style.display = 'none';
    document.getElementById('cat3-list').style.display = 'none';
    document.getElementById(cat + '-list').style.display = 'block';
}