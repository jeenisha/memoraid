// ===================================================================================
// SCRIPT FOR THE MAIN PAGE (index.html)
// ===================================================================================
// This code only runs if an element with the ID 'rec-video' exists on the page.
if (document.getElementById('rec-video')) {
  // --- camera + recognition logic ---
  const video = document.getElementById('rec-video');
  const canvas = document.getElementById('rec-canvas');
  const resultBox = document.getElementById('rec-result');

  let stream = null;
  let detectInterval = null;
  const RECOGNIZE_INTERVAL_MS = 4000; // 4s

  async function openCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = stream;
    await video.play();
  }

  function closeCamera() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    video.pause();
  }

  async function captureFrameAsFile() {
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => {
      canvas.toBlob(blob => {
        const filename = `capture_${Date.now()}.jpg`;
        const file = new File([blob], filename, { type: 'image/jpeg' });
        resolve(file);
      }, 'image/jpeg', 0.9);
    });
  }

  async function sendFrameForRecognition(file) {
    const form = new FormData();
    form.append('file', file, file.name);
    const resp = await fetch('/recognize', { method: 'POST', body: form });
    return resp.json();
  }

  async function doRecognitionOnce() {
    if (!stream) return;
    try {
      const file = await captureFrameAsFile();
      const json = await sendFrameForRecognition(file);
      if (json && json.status === 'success') {
        const faces = json.faces;
        if (Array.isArray(faces)) {
          processFaces(faces);
        } else if (faces && faces.faces) {
          processFaces(faces.faces);
        } else {
          resultBox.innerText = "No faces detected.";
        }
      } else {
        resultBox.innerText = "Recognition error: " + (json.message || "unknown");
      }
    } catch (e) {
      resultBox.innerText = "Recognition exception: " + e.message;
    }
  }

  function processFaces(facesArr) {
    if (!facesArr || facesArr.length === 0) {
      resultBox.innerText = "No faces detected.";
      return;
    }
    const lines = facesArr.map(face => {
      if (face.name && face.name !== "Unknown") {
        return `${face.name} (${face.relation})`;
      } else {
        return "Unknown";
      }
    });
    resultBox.innerText = lines.join('\n');
  }

  document.getElementById('rec-start').addEventListener('click', async () => {
    if (!stream) await openCamera();
    if (detectInterval) clearInterval(detectInterval);
    detectInterval = setInterval(doRecognitionOnce, RECOGNIZE_INTERVAL_MS);
  });

  document.getElementById('rec-stop').addEventListener('click', () => {
    if (detectInterval) clearInterval(detectInterval);
    detectInterval = null;
    closeCamera();
  });

  document.getElementById('rec-capture').addEventListener('click', async () => {
    if (!stream) await openCamera();
    await doRecognitionOnce();
  });

  // --- Caregiver login modal ---
  const loginModal = document.getElementById('login-modal');
  const loginPassword = document.getElementById('login-password');
  const loginMsg = document.getElementById('login-msg');

  document.getElementById('caregiver-login').addEventListener('click', () => {
    loginPassword.value = '';
    loginMsg.innerText = '';
    loginModal.style.display = 'flex';
    loginPassword.focus();
  });

  document.getElementById('login-cancel').addEventListener('click', () => {
    loginModal.style.display = 'none';
  });

  document.getElementById('login-submit').addEventListener('click', async () => {
    const p = loginPassword.value.trim();
    if (!p) { loginMsg.innerText = 'Enter password'; return; }
    const form = new FormData();
    form.append('password', p);
    const resp = await fetch('/login', { method: 'POST', body: form });
    const j = await resp.json();
    if (j && j.status === 'success') {
      loginModal.style.display = 'none';
      window.location.href = '/dashboard';
    } else {
      loginMsg.innerText = j.message || 'Invalid password';
    }
  });

  // --- Reminders polling + browser alert + TTS ---
  let triggeredSet = new Set();

  async function pollReminders() {
    try {
      const resp = await fetch('/get_reminders');
      const data = await resp.json();
      if (data && typeof data === 'object') {
        const now = new Date();
        const hh = now.getHours().toString().padStart(2, '0');
        const mm = now.getMinutes().toString().padStart(2, '0');
        const cur = `${hh}:${mm}`;
        for (const [user, arr] of Object.entries(data)) {
          if (!Array.isArray(arr)) continue;
          for (const r of arr) {
            const t = ('' + (r.time || '')).trim();
            const msg = ('' + (r.message || '')).trim();
            const key = `${user}___${t}___${msg}`;
            if (t === cur && !triggeredSet.has(key)) {
              try {
                alert(`Reminder for ${user}: ${msg}`);
              } catch (e) {}
              try {
                if ('speechSynthesis' in window) {
                  const utter = new SpeechSynthesisUtterance(msg);
                  window.speechSynthesis.speak(utter);
                }
              } catch (e) {}
              triggeredSet.add(key);
            }
          }
        }
        if (triggeredSet.size > 1000) triggeredSet.clear();
      }
    } catch (e) {
      console.log("Poll reminders error:", e);
    }
  }

  setInterval(pollReminders, 30 * 1000);
  pollReminders();
}


// ===================================================================================
// SCRIPT FOR THE DASHBOARD PAGE (dashboard.html)
// ===================================================================================
// This code only runs if an element with the ID 'upload-add' exists on the page.
if (document.getElementById('upload-add')) {
  // --- Add Person via upload ---
  document.getElementById('upload-add').addEventListener('click', async () => {
    const name = document.getElementById('upload-name').value.trim();
    const relation = document.getElementById('upload-relation').value.trim();
    const fileEl = document.getElementById('upload-file');
    const msgDiv = document.getElementById('upload-msg');

    if (!name || !relation) { msgDiv.innerText = 'Name & relation required'; return; }
    if (!fileEl.files || fileEl.files.length === 0) { msgDiv.innerText = 'Select file'; return; }

    const form = new FormData();
    form.append('name', name);
    form.append('relation', relation);
    form.append('file', fileEl.files[0], fileEl.files[0].name);

    const res = await fetch('/add_person', { method: 'POST', body: form });
    const j = await res.json();
    if (j.status === 'success') {
      msgDiv.innerText = j.message;
      document.getElementById('upload-name').value = '';
      document.getElementById('upload-relation').value = '';
      fileEl.value = '';
    } else {
      msgDiv.innerText = j.message || 'Error';
    }
  });

  // --- Camera capture for add person ---
  const addVideo = document.getElementById('add-video');
  const addCanvas = document.getElementById('add-canvas');
  let addStream = null;

  document.getElementById('add-open').addEventListener('click', async () => {
    addStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    addVideo.srcObject = addStream;
    await addVideo.play();
  });

  document.getElementById('add-close').addEventListener('click', () => {
    if (addStream) addStream.getTracks().forEach(t => t.stop());
    addStream = null;
    addVideo.pause();
  });

  document.getElementById('add-capture').addEventListener('click', async () => {
    if (!addStream) return alert('Open camera first');
    addCanvas.width = addVideo.videoWidth || 320;
    addCanvas.height = addVideo.videoHeight || 240;
    addCanvas.getContext('2d').drawImage(addVideo, 0, 0, addCanvas.width, addCanvas.height);
    const dataUrl = addCanvas.toDataURL('image/jpeg', 0.9);
    document.getElementById('added-preview').innerHTML = `<img src="${dataUrl}" width="160" />`;
  });

  document.getElementById('add-submit').addEventListener('click', async () => {
    const name = document.getElementById('cam-name').value.trim();
    const relation = document.getElementById('cam-relation').value.trim();
    if (!name || !relation) { alert('Name & relation required'); return; }
    addCanvas.toBlob(async (blob) => {
      const filename = `cam_upload_${Date.now()}.jpg`;
      const form = new FormData();
      form.append('name', name);
      form.append('relation', relation);
      form.append('file', new File([blob], filename, { type: 'image/jpeg' }));
      const res = await fetch('/add_person', { method: 'POST', body: form });
      const j = await res.json();
      if (j.status === 'success') {
        alert('Person added: ' + j.message);
        document.getElementById('cam-name').value = '';
        document.getElementById('cam-relation').value = '';
        document.getElementById('added-preview').innerText = 'No preview';
      } else {
        alert('Error: ' + (j.message || 'unknown'));
      }
    }, 'image/jpeg', 0.9);
  });

  // --- Reminders CRUD (Add + display) ---
  async function loadReminders() {
    const res = await fetch('/get_reminders');
    const data = await res.json();
    const out = [];
    for (const [user, arr] of Object.entries(data || {})) {
      if (!Array.isArray(arr)) continue;
      arr.forEach((r, i) => {
        out.push(`<div><b>${user}</b> @ ${r.time} : ${r.message}  <button onclick="deleteRem('${user}',${i})">Del</button></div>`);
      });
    }
    document.getElementById('rem-list').innerHTML = out.join('') || 'No reminders';
  }
  
  // NOTE: deleteRem is defined globally below so the onclick attribute can find it.

  document.getElementById('rem-add').addEventListener('click', async () => {
    const user = document.getElementById('rem-user').value.trim();
    const time = document.getElementById('rem-time').value.trim();
    const msg = document.getElementById('rem-message').value.trim();
    if (!user || !time || !msg) return alert('Fill all fields');
    const form = new FormData();
    form.append('user', user);
    form.append('time', time);
    form.append('message', msg);
    const res = await fetch('/add_reminder', { method: 'POST', body: form });
    const j = await res.json();
    if (j.status === 'success') {
      alert('Reminder added');
      document.getElementById('rem-user').value = '';
      document.getElementById('rem-time').value = '';
      document.getElementById('rem-message').value = '';
      loadReminders();
    } else alert('Error adding reminder');
  });

  // init
  loadReminders();
}

// This function must be GLOBAL so the HTML 'onclick' can find it.
async function deleteRem(user, idx) {
  const form = new FormData();
  form.append('user', user);
  form.append('index', idx);
  const res = await fetch('/delete_reminder', { method: 'POST', body: form });
  const j = await res.json();
  if (j.status === 'success') {
    // Reload reminders by finding the `rem-list` element, which only exists on the dashboard.
    // This is a safe way to call a function that should only run on the dashboard.
    if (document.getElementById('rem-list')) {
       // We can't call loadReminders() directly because it's not global, so we re-implement its core logic.
       const reloadRes = await fetch('/get_reminders');
       const data = await reloadRes.json();
       const out = [];
       for (const [user, arr] of Object.entries(data || {})) {
         if (!Array.isArray(arr)) continue;
         arr.forEach((r, i) => {
           out.push(`<div><b>${user}</b> @ ${r.time} : ${r.message}  <button onclick="deleteRem('${user}',${i})">Del</button></div>`);
         });
       }
       document.getElementById('rem-list').innerHTML = out.join('') || 'No reminders';
    }
  } else alert('Delete failed');
}