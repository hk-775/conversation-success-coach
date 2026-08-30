(() => {
    "use strict";

    const menuButton = document.querySelector(".mobile-menu-button");
    const siteLinks = document.querySelector("#site-links");
    if (menuButton && siteLinks) {
        menuButton.addEventListener("click", () => {
            const open = menuButton.getAttribute("aria-expanded") === "true";
            menuButton.setAttribute("aria-expanded", String(!open));
            siteLinks.classList.toggle("open", !open);
        });
        siteLinks.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                menuButton.setAttribute("aria-expanded", "false");
                siteLinks.classList.remove("open");
            });
        });
    }

    const revealItems = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12 },
        );
        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("visible"));
    }

    const modeTabs = Array.from(document.querySelectorAll("[data-mode-tab]"));
    const modePanels = Array.from(document.querySelectorAll("[data-mode-panel]"));
    const selectMode = (mode) => {
        modeTabs.forEach((tab) => {
            const active = tab.dataset.modeTab === mode;
            tab.classList.toggle("active", active);
            tab.setAttribute("aria-selected", String(active));
            tab.tabIndex = active ? 0 : -1;
        });
        modePanels.forEach((panel) => {
            const active = panel.dataset.modePanel === mode;
            panel.classList.toggle("active", active);
            panel.hidden = !active;
        });
    };
    modeTabs.forEach((tab, index) => {
        tab.addEventListener("click", () => selectMode(tab.dataset.modeTab));
        tab.addEventListener("keydown", (event) => {
            if (!["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"].includes(event.key)) {
                return;
            }
            event.preventDefault();
            const delta = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
            const next = (index + delta + modeTabs.length) % modeTabs.length;
            modeTabs[next].focus();
            selectMode(modeTabs[next].dataset.modeTab);
        });
    });
})();
