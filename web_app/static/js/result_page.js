// Behavior for the select all button
$("#select-all").click(function(event) {
    if (this.checked) {
        $(".selection-item").each(function(event) {
                this.checked = true;
        });
    } else {
        $(".selection-item").each(function(event) {
                this.checked = false;
        });
    }
});

// Functionality for Download select button
$("#download-selected").click(function(event) {
    let data = $(".selection-item").filter(function() {
        return this.checked;
    }).map(function() {
        return this.value;
    }).get();
    
    if (data.length === 0) {
        alert("No files selected");
        return;
    }

    // Download the file.
    fetch("/download/all", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"ids": data})
    })
    .then(resp => resp.blob())
    .then(blob => {
        // Get the file from the request and download it.
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = 'download.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    });
});
