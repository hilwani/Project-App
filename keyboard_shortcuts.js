// keyboard_shortcuts.js
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'n') {
        // Create a new task
        window.location.href = '/create-task';
    }
    if (event.ctrlKey && event.key === 'm') {
        // Mark task as complete
        document.getElementById('mark-complete').click();
    }
});