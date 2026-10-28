function updateFavicon(theme) {
    const faviconLink = document.getElementById("dynamic-favicon");
    
    if (faviconLink) {
        faviconLink.href = `/static/images/favicon_${theme}.png`;
    }
}

(function () {
    const savedTheme = localStorage.getItem("theme");

    let theme = "light";

    if (savedTheme) {
        theme = savedTheme;
    } else {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

        theme = prefersDark ? "dark" : "light";
    }

    document.documentElement.setAttribute("data-theme", theme);
    
    updateFavicon(theme);
})();

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", newTheme);

    localStorage.setItem("theme", newTheme);

    updateThemeIcon(newTheme);
    updateFavicon(newTheme);
}

function updateThemeIcon(theme) {
    const iconBtn = document.getElementById("theme-toggle-icon");

    if (iconBtn) {
        iconBtn.setAttribute("data-lucide", theme === "dark" ? "sun" : "moon");

        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    
    updateThemeIcon(currentTheme);
    updateFavicon(currentTheme);
});