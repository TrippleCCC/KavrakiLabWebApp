// Define function for periodically checking download progress
async function init_ping_download(data) {
    // First make a request to init the download
    const response = await fetch("/download/init", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({"downloadType": "singleconf", "ids": data})
    });

    const data2 = await response.json();
    console.log(data2);
    const id = data2["thread-id"];

    // Setup buttons.
    $("#cancel-download").off("click").click(function() {
        fetch("/download/cancel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({"thread-id": id})
        })
        .then(resp => {
            $("#DownloadModal").modal("hide");
        });
    });

    // This recursive function continously ping the server to get the
    // status of the file being zipped. When the ziping process is stopped
    // the function returns
    async function ping_loop() {
        var resp = await fetch("/download/progress", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({"thread-id": id})
        });

        var pro = await resp.json();
        console.log(pro);
        if ("error" in pro)
            return

        // Set the progress bar
        $(".progress-bar").css("width", (pro["progress"]*100/pro["total"]).toString()+"%");
        $("#loading-status").html(
                pro["progress"] + " file(s) out of " + pro["total"] + " zipped.");

        if (pro["progress"] == pro["total"])
            console.log("Finished Zip");
        else {
            // Keep pinging the progress until zipping is done
            setTimeout(ping_loop, 1000);
            return;
        }

        // Now download the file
        $("#loading-status").html("Zipped all " + pro["total"].toString() + " file(s).");
        $("#loading-spinner").css("visibility", "visible");
        $("#cancel-download").prop("disabled", true);
        fetch("/download/get_zip", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({"thread-id": id})
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
            $("#loading-spinner").css("visibility", "hidden");
            $("#close-button").prop("disabled", false);
        });
    };
    
    setTimeout(ping_loop, 1000);
}

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

    // Open download modal and Init zip download
    $(".progress-bar").css("width", "0%");
    $("#loading-status").html("");
    $("#close-button").prop("disabled", true);
    $("#cancel-download").prop("disabled", false);
    $('#DownloadModal').modal({show: true});
    init_ping_download(data);
});