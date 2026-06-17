// Conexión WebSocket
const socket = new WebSocket(`ws://${location.host}/ws`);

socket.onmessage = function(event) {
    if (event.data === "update") {
        fetchGraphList(true); // Refresca y muestra el último gráfico
    }
};

socket.onopen = () => console.log("WebSocket conectado.");
socket.onerror = error => console.error("WebSocket error:", error);
socket.onclose = () => console.log("WebSocket cerrado.");

// Variables de estado
let graphs = [];
let currentIndex = 0;

// Obtener lista de gráficos desde /latest
async function fetchGraphList(goToLast = false) {
    try {
        const response = await fetch("/latest");
        const data = await response.json();
        graphs = data.graphs || [];

        if (graphs.length === 0) {
            document.getElementById("no-graphs-message").style.display = "block";
        } else {
            document.getElementById("no-graphs-message").style.display = "none";
        }

        if (goToLast) {
            currentIndex = graphs.length - 1;
        }

        updateGraphDisplay();
    } catch (err) {
        console.error("Error al cargar gráficos:", err);
    }
}

// Mostrar el gráfico actual
function updateGraphDisplay() {
    const img = document.getElementById("graph-image");
    const html = document.getElementById("graph-html");

    img.style.display = "none";
    html.style.display = "none";

    if (graphs.length === 0) return;

    const graph = graphs[currentIndex];
    const title = graph.title;

    if (graph.type === "image") {
        img.src = `/static/images/${title}.png`;
        img.style.display = "block";
    } else if (graph.type === "html") {
        html.src = `/static/html/${title}.html`;
        html.style.display = "block";
    }
}


// Navegación
document.getElementById("first-image").addEventListener("click", () => {
    currentIndex = 0;
    updateGraphDisplay();
});

document.getElementById("prev-image").addEventListener("click", () => {
    if (currentIndex > 0) currentIndex--;
    updateGraphDisplay();
});

document.getElementById("next-image").addEventListener("click", () => {
    if (currentIndex < graphs.length - 1) currentIndex++;
    updateGraphDisplay();
});

document.getElementById("last-image").addEventListener("click", () => {
    currentIndex = graphs.length - 1;
    updateGraphDisplay();
});

// Pantalla completa
document.getElementById("fullscreen").addEventListener("click", () => {
    const container = document.getElementById("graph-display");
    if (container.requestFullscreen) container.requestFullscreen();
    else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
    else if (container.msRequestFullscreen) container.msRequestFullscreen();
    else if (container.mozRequestFullScreen) container.mozRequestFullScreen();
});

// Carga inicial
fetchGraphList();
