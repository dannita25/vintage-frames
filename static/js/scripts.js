// JavaScript to handle modal population for user management (backend)
document.addEventListener('DOMContentLoaded', function () {
    // User Modal Handling
    const editButtons = document.querySelectorAll('.edit-user-btn');
    const editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));

    editButtons.forEach(button => {
        button.addEventListener('click', function () {
            const username = this.dataset.username; // Get username from the button attb
            const email = this.dataset.email; // Get email from the button attb
            
            // Populate modal fields
            document.getElementById('modalUsername').value = username;
            document.getElementById('modalEmail').value = email;
            document.getElementById('modalNewUsername').value = username;

            // Set form action dynamically
            const form = document.getElementById('editUserForm');
            form.action = `/admin/edit_user/${username}`;

            // Show the modal
            editUserModal.show();
        });
    });
});








