// Example: Add a confirmation dialog before deleting a task
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-task');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this task?')) {
                event.preventDefault();
            }
        });
    });
});