// Se establece la conexión con el WebSocket del servidor
const socket = new WebSocket(`ws://${location.host}/ws`);

socket.onmessage = function(event) {
    if (event.data === "update") {
        fetchGraphList(true); // Cuando hay actualización, recarga y muestra el último gráfico
    }
};

socket.onopen = function() {
    console.log("Conexión WebSocket establecida.");
};

socket.onerror = function(error) {
    console.error("Error en WebSocket:", error);
};

socket.onclose = function() {
    console.log("Conexión WebSocket cerrada.");
};

// Variables para manejar la lista de gráficos
let graphs = [];
let currentIndex = 0;

// Obtener la lista de gráficos disponibles
async function fetchGraphList(goToLast = false) {
    const response = await fetch("/latest");
    const data = await response.json();

    graphs = data.graphs || [];

    if (graphs.length === 0) {
        document.getElementById("no-graphs-message").style.display = "block";
    } else {
        document.getElementById("no-graphs-message").style.display = "none";
    }

    if (goToLast) {
        currentIndex = graphs.length - 1; // Ir al último gráfico generado
    }

    updateGraphDisplay();
}

// Función para actualizar la vista del gráfico
function updateGraphDisplay() {
    let img = document.getElementById("graph-image");
    let html = document.getElementById("graph-html");

    img.style.display = "none";
    html.style.display = "none";

    if (graphs.length === 0) return;

    let graph = graphs[currentIndex];

    if (graph.type === "image") {
        img.src = `/static/images/${graph.name}`;
        img.style.display = "block";
    } else if (graph.type === "html") {
        html.src = `/static/html/${graph.name}`;
        html.style.display = "block";
    }
}

// Botones de navegación
document.getElementById("first-image").addEventListener("click", () => {
    currentIndex = 0;
    updateGraphDisplay();
});

document.getElementById("prev-image").addEventListener("click", () => {
    if (currentIndex > 0) {
        currentIndex--;
    } else {
        currentIndex = 0;
    }
    updateGraphDisplay();
});

document.getElementById("next-image").addEventListener("click", () => {
    if (currentIndex < graphs.length - 1) {
        currentIndex++;
        updateGraphDisplay();
    }
});

document.getElementById("last-image").addEventListener("click", () => {
    currentIndex = graphs.length - 1;
    updateGraphDisplay();
});

// Pantalla completa
document.getElementById("fullscreen").addEventListener("click", () => {
    let container = document.getElementById("graph-display");
    if (container.requestFullscreen) {
        container.requestFullscreen();
    } else if (container.mozRequestFullScreen) {
        container.mozRequestFullScreen();
    } else if (container.webkitRequestFullscreen) {
        container.webkitRequestFullscreen();
    } else if (container.msRequestFullscreen) {
        container.msRequestFullscreen();
    }
});

// Cargar los gráficos al inicio
fetchGraphList();
