// Función para convertir el título en una versión segura (igual que en Python)
function sanitizeTitle(title) {
    return title.replace(/ /g, "_").replace(/[^a-zA-Z0-9_-]/g, "_");
}

// Manejar la edición del título en el input
async function handleTitleEdit(event, inputElement) {
    if (event.key === "Enter") {
        const oldTitle = inputElement.dataset.oldTitle;
        const newTitle = inputElement.value.trim();

        if (!newTitle || newTitle === oldTitle) return;

        try {
            const response = await fetch("/rename", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ old_title: oldTitle, new_title: newTitle })
            });

            const result = await response.json();

            if (response.ok) {
                const previewItem = inputElement.closest(".preview-item");

                // Sanitizar título (igual que en backend)
                const sanitizedTitle = sanitizeTitle(newTitle);

                // Actualizar imagen
                const img = previewItem.querySelector("img");
                if (img) {
                    img.src = `/static/images/${sanitizedTitle}.png`;
                }

                // Actualizar enlace de descarga
                const downloadLink = previewItem.querySelector('a[href$=".png"]');
                if (downloadLink) {
                    downloadLink.href = `/static/images/${sanitizedTitle}.png`;
                }

                // Actualizar botón "Ver en grande"
                const viewButtonLink = previewItem.querySelectorAll("a")[1];
                if (viewButtonLink) {
                    const isInteractive = viewButtonLink.href.includes(".html");
                    viewButtonLink.href = isInteractive
                        ? `/static/html/${sanitizedTitle}.html`
                        : `/static/images/${sanitizedTitle}.png`;
                }

                // Actualizar dataset
                inputElement.dataset.oldTitle = sanitizedTitle;

                // ✅ Mostrar mensaje de éxito
                const message = document.createElement("div");
                message.className = "rename-success";
                message.textContent = "✅ Título actualizado";
                previewItem.appendChild(message);
                setTimeout(() => message.remove(), 2000);

                // 🔁 Refrescar la lista de gráficos si es necesario
                if (typeof fetchGraphList === "function") {
                    fetchGraphList();
                }

            } else {
                alert(result.error || "⚠️ Error al renombrar.");
            }

        } catch (err) {
            console.error("❌ Error:", err);
            alert("❌ No se pudo conectar al servidor.");
        }
    }
}


