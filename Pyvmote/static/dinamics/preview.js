function handleTitleEdit(event, input) {
    if (event.key === "Enter") {
        const oldTitle = input.getAttribute("data-old-title");
        const newTitle = input.value;

        if (oldTitle === newTitle) {
            alert("El título no ha cambiado.");
            return;
        }

        fetch("/rename", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ old_title: oldTitle, new_title: newTitle })
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                input.setAttribute("data-old-title", newTitle);
                alert("Título actualizado con éxito.");
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(err => {
            console.error(err);
            alert("Error al actualizar el título.");
        });
    }
}
