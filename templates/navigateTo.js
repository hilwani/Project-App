function displayBreadcrumbs() {
    // Display breadcrumbs as clickable links.
    if (sessionStorage.getItem('breadcrumbs')) {
        const breadcrumbs = JSON.parse(sessionStorage.getItem('breadcrumbs'));
        const breadcrumbLinks = breadcrumbs.map(crumb => 
            `<a href="javascript:void(0);" onclick="navigateTo('${crumb}')" style="text-decoration: none; color: inherit;">${crumb}</a>`
        ).join(' > ');
        document.write(`
        <script>
        function navigateTo(page) {
            const pages = {
                "Dashboard": "Dashboard",
                "Projects": "Projects",
                "Tasks": "Tasks",
                "Reports": "Reports",
                "Notifications": "Notifications",
                "Admin": "Admin"
            };
            if (pages[page]) {
                window.location.hash = page;
                window.location.reload();
            }
        }
        </script>
        <strong>Navigation:</strong> ${breadcrumbLinks}
        `);
    }
}