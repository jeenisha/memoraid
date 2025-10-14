
// --- Recognize section ---
const recVideo = document.getElementById("rec-video");
const recCanvas = document.getElementById("rec-canvas");
const recStart = document.getElementById("rec-start");
const recCapture = document.getElementById("rec-capture");
const recStop = document.getElementById("rec-stop");
const recResult = document.getElementById("rec-result");
let recStream = null;

async function openRecCam() {
  if (recStream) return;
  recStream = await navigator.mediaDevices.getUserMedia({ video: true });
  recVideo.srcObject = recStream;
}

function closeRecCam() {
  if (!recStream) return;
  recStream.getTracks().forEach(t => t.stop());
  recVideo.srcObject = null;
  recStream = null;
}

recStart.onclick = async () => {
  try {
    await openRecCam();
    recResult.textContent = "Camera opened. Click Capture to take one frame.";
  } catch (e) {
    alert("Could not open camera: " + e.message);
  }
};

recStop.onclick = () => {
  closeRecCam();
  recResult.textContent = "Camera closed.";
};

recCapture.onclick = async () => {
  if (!recStream) return alert("Start the camera first");
  recCanvas.width = recVideo.videoWidth;
  recCanvas.height = recVideo.videoHeight;
  const ctx = recCanvas.getContext("2d");
  ctx.drawImage(recVideo, 0, 0, recCanvas.width, recCanvas.height);

  // convert to blob and send
  recCanvas.toBlob(async (blob) => {
    const fd = new FormData();
    fd.append("file", blob, "capture.jpg");
    recResult.textContent = "Recognizing...";
    try {
      const res = await fetch("/recognize", { method: "POST", body: fd });
      const data = await res.json();
      if (data.status === "success") {
        const faces = data.faces || [];
        if (faces.length === 0) {
          recResult.textContent = "No faces detected.";
        } else {
          // show first match (or list)
          recResult.innerHTML = faces.map((f, i) => {
            if (f.status === "recognized") {
              return `<div class="match">✅ ${f.name} — ${f.relation} (confidence: ${ (f.confidence || 0).toFixed(2) })</div>`;
            } else if (f.status === "unknown") {
              return `<div class="match">❌ Unknown</div>`;
            } else {
              return `<div class="match">⚠️ ${f.status}</div>`;
            }
          }).join("");
        }
      } else {
        recResult.textContent = "Error: " + (data.message || "unknown");
      }
    } catch (err) {
      recResult.textContent = "Recognition error: " + err.message;
    } finally {
      // after one capture we close camera as requested
      closeRecCam();
    }
  }, "image/jpeg");
};

// --- Add person (upload) ---
document.getElementById("upload-add").onclick = async () => {
  const name = document.getElementById("upload-name").value.trim();
  const relation = document.getElementById("upload-relation").value.trim();
  const fileInput = document.getElementById("upload-file");

  if (!name || !relation) return alert("Enter name and relation");
  if (!fileInput.files || fileInput.files.length === 0) return alert("Choose a file");

  const fd = new FormData();
  fd.append("name", name);
  fd.append("relation", relation);
  fd.append("file", fileInput.files[0]);

  const res = await fetch("/add_person", { method: "POST", body: fd });
  const data = await res.json();
  alert(data.message || JSON.stringify(data));
  // optionally clear inputs
  fileInput.value = "";
  document.getElementById("upload-name").value = "";
  document.getElementById("upload-relation").value = "";
};

// --- Add person (camera) ---
const addVideo = document.getElementById("add-video");
const addCanvas = document.getElementById("add-canvas");
const addOpen = document.getElementById("add-open");
const addCapture = document.getElementById("add-capture");
const addClose = document.getElementById("add-close");
const addSubmit = document.getElementById("add-submit");
const addedPreview = document.getElementById("added-preview");
let addStream = null;
let addedBlob = null;

addOpen.onclick = async () => {
  if (addStream) return;
  try {
    addStream = await navigator.mediaDevices.getUserMedia({ video: true });
    addVideo.srcObject = addStream;
    addVideo.style.display = "block";
    addedPreview.textContent = "Camera opened. Click Capture Image to take a photo.";
  } catch (e) {
    alert("Could not open camera: " + e.message);
  }
};

addClose.onclick = () => {
  if (addStream) {
    addStream.getTracks().forEach(t => t.stop());
    addStream = null;
  }
  addVideo.style.display = "none";
  addedPreview.textContent = "Camera closed.";
};

addCapture.onclick = async () => {
  if (!addStream) return alert("Open camera first");
  addCanvas.width = addVideo.videoWidth;
  addCanvas.height = addVideo.videoHeight;
  const ctx = addCanvas.getContext("2d");
  ctx.drawImage(addVideo, 0, 0, addCanvas.width, addCanvas.height);

  addCanvas.toBlob((blob) => {
    addedBlob = blob;
    const url = URL.createObjectURL(blob);
    addedPreview.innerHTML = `<img src="${url}" class="thumb" /> <div>Preview captured image</div>`;
  }, "image/jpeg");
};

addSubmit.onclick = async () => {
  const name = document.getElementById("cam-name").value.trim();
  const relation = document.getElementById("cam-relation").value.trim();
  if (!name || !relation) return alert("Enter name and relation");
  if (!addedBlob) return alert("Capture an image first");

  const fd = new FormData();
  fd.append("name", name);
  fd.append("relation", relation);
  fd.append("file", addedBlob, "cam_capture.jpg");

  const res = await fetch("/add_person", { method: "POST", body: fd });
  const data = await res.json();
  alert(data.message || JSON.stringify(data));
  // clear and close camera
  addedBlob = null;
  addClose.onclick();
  document.getElementById("cam-name").value = "";
  document.getElementById("cam-relation").value = "";
  addedPreview.textContent = "No preview";
};

// --- Reminders: fetch, add, edit, delete ---
async function fetchReminders() {
  const res = await fetch("/get_reminders");
  const data = await res.json();
  const container = document.getElementById("rem-list");
  container.innerHTML = "";

  for (const user in data) {
    data[user].forEach((r, idx) => {
      const div = document.createElement("div");
      div.className = "rem-item";
      div.innerHTML = `<strong>${user}</strong> — ${r.time} — ${r.message}
        <button class="rem-edit">Edit</button>
        <button class="rem-delete">Delete</button>`;
      const editBtn = div.querySelector(".rem-edit");
      const delBtn = div.querySelector(".rem-delete");

      editBtn.onclick = async () => {
        const newTime = prompt("New time (HH:MM):", r.time);
        const newMsg = prompt("New message:", r.message);
        if (newTime === null && newMsg === null) return;
        const fd = new FormData();
        fd.append("user", user);
        fd.append("index", idx);
        if (newTime) fd.append("new_time", newTime);
        if (newMsg) fd.append("new_message", newMsg);
        const res = await fetch("/edit_reminder", { method: "POST", body: fd });
        const d = await res.json();
        alert(d.message || JSON.stringify(d));
        fetchReminders();
      };

      delBtn.onclick = async () => {
        const fd = new FormData();
        fd.append("user", user);
        fd.append("index", idx);
        const res = await fetch("/delete_reminder", { method: "POST", body: fd });
        const d = await res.json();
        alert(d.message || JSON.stringify(d));
        fetchReminders();
      };

      container.appendChild(div);
    });
  }
}

document.getElementById("rem-add").onclick = async () => {
  const user = document.getElementById("rem-user").value.trim();
  const time = document.getElementById("rem-time").value;
  const message = document.getElementById("rem-message").value.trim();
  if (!user || !time || !message) return alert("Fill all fields");
  const fd = new FormData();
  fd.append("user", user);
  fd.append("time", time);
  fd.append("message", message);
  const res = await fetch("/add_reminder", { method: "POST", body: fd });
  const d = await res.json();
  alert(d.message || JSON.stringify(d));
  document.getElementById("rem-user").value = "";
  document.getElementById("rem-time").value = "";
  document.getElementById("rem-message").value = "";
  fetchReminders();
};

// initial load
fetchReminders();
