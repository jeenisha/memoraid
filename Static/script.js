// ===================================================================================
// SCRIPT FOR THE MAIN PAGE (index.html)
// This code only runs if an element with the ID 'rec-video' exists on the page.
// ===================================================================================
if (document.getElementById('rec-video')) {

    // --- Camera + Recognition Logic ---
    const video = document.getElementById('rec-video');
    const canvas = document.getElementById('rec-canvas');
    const resultBox = document.getElementById('rec-result');
    let stream = null;
    let detectInterval = null;
    const RECOGNIZE_INTERVAL_MS = 4000;

    async function openCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = stream;
            await video.play();
        } catch (e) {
            alert('Could not open camera: ' + e.message);
        }
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

    // --- Caregiver Login Modal Logic ---
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
        if (!p) {
            loginMsg.innerText = 'Enter password';
            return;
        }
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

    // --- Reminders Polling and Notifications ---
    const notifiedReminders = new Set();
    async function pollReminders() {
        try {
            const reminders = await fetch('/get_reminders').then(res => res.json());
            const now = new Date();

            reminders.forEach(r => {
                const reminderTime = new Date(r.datetime);
                if (reminderTime <= now && !notifiedReminders.has(r.id)) {
                    notifiedReminders.add(r.id);
                    showNotification(r);
                    try {
                        if ('speechSynthesis' in window) {
                            const utter = new SpeechSynthesisUtterance(`Reminder for ${r.user}: ${r.message}`);
                            window.speechSynthesis.speak(utter);
                        }
                    } catch (e) {
                        console.error("Speech synthesis error:", e);
                    }
                }
            });
        } catch (e) {
            console.error("Poll reminders error:", e);
        }
    }

    function showNotification(reminder) {
        const container = document.getElementById('notification-area');
        const notif = document.createElement('div');
        notif.className = 'notification';
        notif.innerHTML = `<p><strong>Reminder for ${reminder.user}:</strong></p><p>${reminder.message}</p>`;
        container.prepend(notif);
        setTimeout(() => {
            notif.style.opacity = '0';
            setTimeout(() => notif.remove(), 500);
        }, 30000);
    }

    setInterval(pollReminders, 15 * 1000);
    pollReminders();
}


// ===================================================================================
// SCRIPT FOR THE DASHBOARD PAGE (dashboard.html)
// This code only runs if an element with the ID 'upload-add' exists on the page.
// ===================================================================================
if (document.getElementById('upload-add')) {

    // --- Reminders CRUD Logic ---
    const remListContainer = document.getElementById('rem-list');

    async function loadReminders() {
        const res = await fetch('/get_reminders');
        const reminders = await res.json();
        remListContainer.innerHTML = '';

        if (reminders.length === 0) {
            remListContainer.innerHTML = 'No reminders set.';
            return;
        }

        reminders.sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

        reminders.forEach(r => {
            const div = document.createElement('div');
            div.className = 'rem-item';
            const displayDate = new Date(r.datetime).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
            div.innerHTML = `<strong>${r.user}</strong> — <span>${displayDate}</span><p>${r.message}</p><button class="delete-btn" data-id="${r.id}">Delete</button>`;
            remListContainer.appendChild(div);
        });
    }

    remListContainer.addEventListener('click', async (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const reminderId = event.target.dataset.id;
            if (!confirm('Are you sure you want to delete this reminder?')) return;

            const fd = new FormData();
            fd.append('id', reminderId);
            const res = await fetch('/delete_reminder', { method: 'POST', body: fd });
            const result = await res.json();

            if (result.status === 'success') {
                loadReminders();
            } else {
                alert('Error: ' + (result.message || 'Could not delete reminder.'));
            }
        }
    });

    document.getElementById('rem-add').addEventListener('click', async () => {
        const user = document.getElementById('rem-user').value.trim();
        const datetime = document.getElementById('rem-datetime').value;
        const message = document.getElementById('rem-message').value.trim();

        if (!user || !datetime || !message) {
            alert('Please fill all fields.');
            return;
        }

        const fd = new FormData();
        fd.append('user', user);
        fd.append('datetime', datetime);
        fd.append('message', message);

        const res = await fetch('/add_reminder', { method: 'POST', body: fd });
        const result = await res.json();

        if (result.status === 'success') {
            document.getElementById('rem-user').value = '';
            document.getElementById('rem-datetime').value = '';
            document.getElementById('rem-message').value = '';
            loadReminders();
        } else {
            alert('Error adding reminder: ' + (result.message || 'Unknown error'));
        }
    });

    loadReminders(); // Initial load for the dashboard

    // --- Add Person via Upload Logic ---
    document.getElementById('upload-add').addEventListener('click', async () => {
        const name = document.getElementById('upload-name').value.trim();
        const relation = document.getElementById('upload-relation').value.trim();
        const fileEl = document.getElementById('upload-file');
        const msgDiv = document.getElementById('upload-msg');

        if (!name || !relation) {
            msgDiv.innerText = 'Name & relation required';
            return;
        }
        if (!fileEl.files || fileEl.files.length === 0) {
            msgDiv.innerText = 'Select file';
            return;
        }

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

    // --- Add Person via Camera Logic ---
    const addVideo = document.getElementById('add-video');
    const addCanvas = document.getElementById('add-canvas');
    let addStream = null;

    document.getElementById('add-open').addEventListener('click', async () => {
        addStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        addVideo.srcObject = addStream;
        await addVideo.play();
    });

    document.getElementById('add-close').addEventListener('click', () => {
        if (addStream) {
            addStream.getTracks().forEach(t => t.stop());
        }
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

        if (!name || !relation) {
            alert('Name & relation required');
            return;
        }

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
}