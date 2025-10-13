// ----------------- Global Streams -----------------
let detectStream, detectInterval;
let addStream;
let recognizeStream;

// ----------------- Detect Face (Live Webcam) -----------------
async function startFaceDetection() {
    const video = document.getElementById("detect-video");
    video.style.display = "block";

    detectStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = detectStream;

    const canvas = document.getElementById("detect-canvas");
    const ctx = canvas.getContext("2d");

    detectInterval = setInterval(async () => {
        if (video.videoWidth === 0) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
            const res = await fetch("/recognize", { method: "POST", body: formData });
            const data = await res.json();
            displayDetectedFaces(data.faces);
        } catch (e) {
            console.log("Recognition error:", e);
        }
    }, 1000);
}

function stopFaceDetection() {
    clearInterval(detectInterval);
    if (detectStream) detectStream.getTracks().forEach(track => track.stop());
    document.getElementById("detect-video").style.display = "none";
}

function displayDetectedFaces(faces = []) {
    const container = document.getElementById("detected-faces");
    container.innerHTML = "";
    if (!faces || faces.length === 0) return container.textContent = "No faces recognized.";

    faces.forEach(f => {
        const div = document.createElement("div");
        div.className = "detected-entry";
        if (f.status === "recognized") {
            div.innerHTML = `✅ <strong>${f.name}</strong> — ${f.relation} <span>(Confidence: ${f.confidence.toFixed(2)})</span>`;
            div.style.color = "green";
        } else {
            div.innerHTML = `❌ Unknown Face`;
            div.style.color = "red";
        }
        container.appendChild(div);
    });
}

// ----------------- Add Face via Webcam -----------------
async function openAddFaceWebcam() {
    const video = document.getElementById("add-face-video");
    video.style.display = "block";

    addStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = addStream;
}

async function captureAddFace() {
    const video = document.getElementById("add-face-video");
    const canvas = document.getElementById("add-face-canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
    return blob;
}

async function addFace() {
    const name = document.getElementById("face-name").value;
    const relation = document.getElementById("face-relation").value;
    const blob = await captureAddFace();
    if (!name || !relation || !blob) return alert("Fill all fields and capture image");

    const formData = new FormData();
    formData.append("name", name);
    formData.append("relation", relation);
    formData.append("file", blob, "webcam.jpg");

    const res = await fetch("/add_face", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);

    stopAddFaceWebcam();
}

function stopAddFaceWebcam() {
    if (addStream) addStream.getTracks().forEach(track => track.stop());
    document.getElementById("add-face-video").style.display = "none";
}

// ----------------- Add Face via File -----------------
async function addFaceFile() {
    const file = document.getElementById("face-file").files[0];
    const name = document.getElementById("face-name").value;
    const relation = document.getElementById("face-relation").value;
    if (!file || !name || !relation) return alert("Please fill all fields and select a file");

    const formData = new FormData();
    formData.append("name", name);
    formData.append("relation", relation);
    formData.append("file", file);

    const res = await fetch("/add_face", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);
}

// ----------------- Recognize Face Webcam -----------------
async function recognizeFaceWebcam() {
    const video = document.getElementById("recognize-video");
    video.style.display = "block";

    recognizeStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = recognizeStream;

    const canvas = document.getElementById("recognize-canvas");
    const ctx = canvas.getContext("2d");

    const captureAndRecognize = async () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        const res = await fetch("/recognize", { method: "POST", body: formData });
        const data = await res.json();
        displayRecognizedFaces(data.faces, blob);
    };

    // Capture frame on click
    video.onclick = captureAndRecognize;
}

async function recognizeFaceFile() {
    const file = document.getElementById("recognize-file").files[0];
    if (!file) return alert("Select a file");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/recognize", { method: "POST", body: formData });
    const data = await res.json();
    displayRecognizedFaces(data.faces, file);
}

// ----------------- Display Recognized Faces -----------------
function displayRecognizedFaces(faces = [], fileOrBlob = null) {
    const container = document.getElementById("recognized-faces");
    container.innerHTML = "";

    if (!faces || faces.length === 0) {
        container.textContent = "No faces recognized.";
        return;
    }

    faces.forEach((f, i) => {
        const div = document.createElement("div");
        div.className = "face-card";

        const img = document.createElement("img");
        if (fileOrBlob) {
            img.src = URL.createObjectURL(fileOrBlob);
            img.onload = () => URL.revokeObjectURL(img.src);
        }

        const h4 = document.createElement("h4");
        h4.textContent = f.status === "recognized" ? f.name : "Unknown";

        const p = document.createElement("p");
        p.textContent = f.status === "recognized" ? f.relation : "";

        const conf = document.createElement("p");
        conf.className = "conf";
        conf.textContent = f.status === "recognized" ? `Confidence: ${f.confidence.toFixed(2)}` : "";

        div.appendChild(img);
        div.appendChild(h4);
        div.appendChild(p);
        div.appendChild(conf);

        container.appendChild(div);
    });
}

// ----------------- Reminders -----------------
async function addReminder() {
    const user = document.getElementById("reminder-user").value;
    const time = document.getElementById("reminder-time").value;
    const message = document.getElementById("reminder-message").value;

    if (!user || !time || !message) return alert("Fill all fields");

    const formData = new FormData();
    formData.append("user", user);
    formData.append("time", time);
    formData.append("message", message);

    const res = await fetch("/add_reminder", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);
    fetchReminders();
}

async function fetchReminders() {
    const res = await fetch("/get_reminders");
    const data = await res.json();
    const container = document.getElementById("reminder-list");
    container.innerHTML = "";

    for (const user in data) {
        data[user].forEach((r, idx) => {
            const div = document.createElement("div");
            div.className = "reminder-item";
            div.innerHTML = `${user} | ${r.time} | ${r.message} <button onclick="deleteReminder('${user}',${idx})">Delete</button>`;
            container.appendChild(div);
        });
    }
}

async function deleteReminder(user, index) {
    const formData = new FormData();
    formData.append("user", user);
    formData.append("index", index);

    const res = await fetch("/delete_reminder", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);
    fetchReminders();
}

// ----------------- Initialize -----------------
fetchReminders();
