document.addEventListener("DOMContentLoaded", () => {
    const userSelect = document.getElementById("user-select");
    const methodSelect = document.getElementById("method-select");
    const getRecommendationsBtn = document.getElementById("get-recommendations");

    const topGamesList = document.getElementById("top-videogames");
    const topCategoriesList = document.getElementById("top-categories");
    const topYearsList = document.getElementById("top-year");
    const similarUsersList = document.getElementById("similar-users");

    // Llenar las opciones de usuarios dinámicamente
    fetch("/users")
        .then(response => response.json())
        .then(data => {
            data.forEach(user => {
                const option = document.createElement("option");
                option.value = user.user_id;
                option.textContent = user.user_id;
                userSelect.appendChild(option);
            });
        });

    // Obtener recomendaciones al hacer clic en el botón
    getRecommendationsBtn.addEventListener("click", () => {
        const userId = userSelect.value;
        const method = methodSelect.value;

        if (!userId || !method) {
            alert("Por favor selecciona un usuario y un método.");
            return;
        }

        fetch(`/recommend?user_id=${userId}&method=${method}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }

                // Mostrar recomendaciones en la interfaz
                topGamesList.innerHTML = data.top_games.map(game => `<li>${game}</li>`).join("");
                topCategoriesList.innerHTML = data.top_categories.map(category => `<li>${category}</li>`).join("");
                topYearsList.innerHTML = data.top_years.map(year => `<li>${year}</li>`).join("");
                similarUsersList.innerHTML = data.similar_users.map(user => `<li>${user}</li>`).join("");
            })
            .catch(err => console.error("Error:", err));
    });
});