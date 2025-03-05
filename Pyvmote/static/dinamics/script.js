// Se establece la conexión con el WebSocket del servidor
const socket = new WebSocket(`ws://${location.host}/ws`);

// Cuando se reciba un mensaje, si es "update", se recarga la página
socket.onmessage = function(event) {
    if (event.data === "update") {
        location.reload();
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