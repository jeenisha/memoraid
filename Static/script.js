// ----------------- Face APIs ----------------
async function addFace() {
    const name = document.getElementById("face-name").value;
    const relation = document.getElementById("face-relation").value;
    const file = document.getElementById("face-file").files[0];

    if (!name || !relation || !file) return alert("Fill all fields");

    const formData = new FormData();
    formData.append("name", name);
    formData.append("relation", relation);
    formData.append("file", file);

    const res = await fetch("/add_face", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);
}

async function recognizeFace() {
    const file = document.getElementById("recognize-file").files[0];
    if (!file) return alert("Select a file");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/recognize", { method: "POST", body: formData });
    const data = await res.json();
    alert(data.message);
}

// ----------------- Reminder APIs ----------------
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

// Fetch & display reminders
async function fetchReminders() {
    const res = await fetch("/get_reminders");
    const data = await res.json();
    const container = document.getElementById("reminder-list");
    container.innerHTML = "";

    for (const user in data) {
        data[user].forEach((r, idx) => {
            const div = document.createElement("div");
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

// Initial load
fetchReminders();
