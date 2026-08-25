let currentCategory = "all";

function toggleMenu() {
    const nav = document.getElementById("mainNav");
    nav.classList.toggle("open");
}

function filterCategory(category, button) {

    currentCategory = category;

    document
        .querySelectorAll(".filter")
        .forEach(item => item.classList.remove("active"));

    button.classList.add("active");

    filterProfiles();
}

function filterProfiles() {

    const query =
        document
            .getElementById("searchInput")
            .value
            .toLowerCase()
            .trim();

    const cards =
        document.querySelectorAll(".profile-card");

    let visible = 0;

    cards.forEach(card => {

        const category =
            card.dataset.category || "";

        const searchable =
            card.dataset.search || "";

        const categoryOK =
            currentCategory === "all" ||
            category.includes(currentCategory);

        const searchOK =
            !query ||
            searchable.includes(query);

        if (categoryOK && searchOK) {

            card.style.display = "";

            visible++;

        } else {

            card.style.display = "none";
        }
    });

    document.getElementById(
        "resultCount"
    ).textContent =
        `${visible} profil${visible > 1 ? "s" : ""}`;
}

function contactUser(name) {

    alert(
        `💬 Messagerie AgriNova\n\n` +
        `Vous souhaitez contacter ${name}.\n\n` +
        `La messagerie réelle sera connectée au backend V6.`
    );
}
