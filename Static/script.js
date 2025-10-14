document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const webcamFeed = document.getElementById('webcamFeed');
    const addWebcamFeed = document.getElementById('addWebcamFeed');

    const startDetectionBtn = document.getElementById('startDetectionBtn');
    const captureFaceBtn = document.getElementById('captureFaceBtn');
    const stopDetectionBtn = document.getElementById('stopDetectionBtn');
    const detectionArea = document.getElementById('detectionArea');
    const recognizedNameSpan = document.getElementById('recognizedName');
    const recognizedRelationSpan = document.getElementById('recognizedRelation');

    const startAddCameraBtn = document.getElementById('startAddCameraBtn');
    const addCameraArea = document.getElementById('addCameraArea');
    const captureAddFaceBtn = document.getElementById('captureAddFaceBtn');
    const stopAddCameraBtn = document.getElementById('stopAddCameraBtn');
    const capturedAddImagePreview = document.getElementById('capturedAddImagePreview');
    const addCameraImageDataInput = document.getElementById('addCameraImageData');
    const addCameraNameInput = document.getElementById('addCameraNameInput');
    const addCameraRelationInput = document.getElementById('addCameraRelationInput');
    const addFromCameraForm = document.getElementById('addFromCameraForm');

    const uploadImageForm = document.getElementById('uploadImageForm');

    const addReminderForm = document.getElementById('addReminderForm');
    const reminderPersonSelect = document.getElementById('reminderPersonSelect');
    const remindersListDiv = document.getElementById('remindersList');

    let currentStream = null; // To manage webcam streams

    // --- Webcam Helper Functions ---
    async function startWebcam(videoElement) {
        if (currentStream) stopWebcam(); // Stop any existing stream first
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = stream;
            currentStream = stream;
            return true;
        } catch (err) {
            console.error("Error accessing webcam: ", err);
            alert("Could not access webcam. Please ensure it's connected and permissions are granted.");
            return false;
        }
    }

    function stopWebcam() {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
        }
    }

    // --- Section 1: Recognize Person ---
    startDetectionBtn.addEventListener('click', async () => {
        if (await startWebcam(webcamFeed)) {
            detectionArea.style.display = 'block';
            startDetectionBtn.style.display = 'none';
            recognizedNameSpan.textContent = 'N/A';
            recognizedRelationSpan.textContent = 'N/A';
        }
    });

    stopDetectionBtn.addEventListener('click', () => {
        stopWebcam();
        detectionArea.style.display = 'none';
        startDetectionBtn.style.display = 'block';
    });

    captureFaceBtn.addEventListener('click', async () => {
        if (!webcamFeed.srcObject) {
            alert("Webcam not active.");
            return;
        }
        
        const canvas = document.createElement('canvas');
        canvas.width = webcamFeed.videoWidth;
        canvas.height = webcamFeed.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(webcamFeed, 0, 0, canvas.width, canvas.height);
        const imageDataURL = canvas.toDataURL('image/jpeg');

        try {
            const response = await fetch('/recognize_face', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageDataURL }),
            });
            const data = await response.json();

            if (data.success && data.person) {
                recognizedNameSpan.textContent = data.person.name;
                recognizedRelationSpan.textContent = data.person.relation;
            } else {
                recognizedNameSpan.textContent = 'Unknown';
                recognizedRelationSpan.textContent = 'N/A';
                alert(data.message || "No face recognized.");
            }
        } catch (error) {
            console.error('Error recognizing face:', error);
            alert('An error occurred during face recognition.');
        } finally {
            stopWebcam();
            detectionArea.style.display = 'none';
            startDetectionBtn.style.display = 'block';
        }
    });

    // --- Section 2: Add Person ---

    // Upload Image Form
    uploadImageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadImageForm);

        try {
            const response = await fetch('/add_person', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            alert(data.message);
            if (data.success) {
                uploadImageForm.reset();
                populateReminderPersonSelect(); // Refresh person select for reminders
            }
        } catch (error) {
            console.error('Error adding person (upload):', error);
            alert('An error occurred while adding the person.');
        }
    });

    // Use Camera for Add Person - Start Camera
    startAddCameraBtn.addEventListener('click', async () => {
        if (await startWebcam(addWebcamFeed)) {
            addCameraArea.style.display = 'block';
            startAddCameraBtn.style.display = 'none';
            capturedAddImagePreview.style.display = 'none';
            addCameraImageDataInput.value = ''; // Clear previous image data
            addCameraNameInput.value = ''; // Clear name
            addCameraRelationInput.value = ''; // Clear relation
        }
    });

    // Use Camera for Add Person - Stop Camera
    stopAddCameraBtn.addEventListener('click', () => {
        stopWebcam();
        addCameraArea.style.display = 'none';
        startAddCameraBtn.style.display = 'block';
        capturedAddImagePreview.style.display = 'none';
    });

    // Use Camera for Add Person - Capture Image
    captureAddFaceBtn.addEventListener('click', () => {
        if (!addWebcamFeed.srcObject) {
            alert("Webcam not active.");
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = addWebcamFeed.videoWidth;
        canvas.height = addWebcamFeed.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(addWebcamFeed, 0, 0, canvas.width, canvas.height);
        const imageDataURL = canvas.toDataURL('image/png'); 

        capturedAddImagePreview.src = imageDataURL;
        capturedAddImagePreview.style.display = 'block';
        addCameraImageDataInput.value = imageDataURL; // Store image data for form submission
        
        stopWebcam(); // Stop webcam after capturing
        addWebcamFeed.srcObject = null; // Clear stream from video element
    });

    // Use Camera for Add Person - Submit Form
    addFromCameraForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!addCameraImageDataInput.value) {
            alert("Please capture an image first.");
            return;
        }

        const formData = new FormData();
        formData.append('name', addCameraNameInput.value);
        formData.append('relation', addCameraRelationInput.value);
        formData.append('image_data_url', addCameraImageDataInput.value);

        try {
            const response = await fetch('/add_person', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            alert(data.message);
            if (data.success) {
                addFromCameraForm.reset();
                capturedAddImagePreview.style.display = 'none';
                addCameraArea.style.display = 'none';
                startAddCameraBtn.style.display = 'block';
                populateReminderPersonSelect(); // Refresh person select for reminders
            }
        } catch (error) {
            console.error('Error adding person (camera):', error);
            alert('An error occurred while adding the person.');
        }
    });
    
    // --- Section 3: Reminders ---

    // Populate Person Select for Reminders
    async function populateReminderPersonSelect() {
        reminderPersonSelect.innerHTML = '<option value="">Select Person</option>';
        try {
            const response = await fetch('/get_all_people_names'); 
            const data = await response.json();
            if (data.success && data.people_names) {
                data.people_names.sort().forEach(name => { // Sort names alphabetically
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    reminderPersonSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error populating person select:', error);
        }
    }

    // Add Reminder Form
    addReminderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(addReminderForm);

        try {
            const response = await fetch('/add_reminder', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            alert(data.message);
            if (data.success) {
                addReminderForm.reset();
                loadRemindersData(); // Refresh reminders list
            }
        } catch (error) {
            console.error('Error adding reminder:', error);
            alert('An error occurred while adding the reminder.');
        }
    });

    // Load and Display Reminders Data
    async function loadRemindersData() {
        try {
            const response = await fetch('/get_reminders');
            const data = await response.json();
            remindersListDiv.innerHTML = ''; // Clear existing list

            if (data.success && data.reminders) {
                let hasReminders = false;
                for (const personName in data.reminders) {
                    if (data.reminders[personName].length > 0) {
                        hasReminders = true;
                        const personRemindersHeader = document.createElement('h4');
                        personRemindersHeader.textContent = personName;
                        remindersListDiv.appendChild(personRemindersHeader);

                        data.reminders[personName].forEach(reminder => {
                            const reminderItem = document.createElement('div');
                            reminderItem.classList.add('reminder-item');
                            reminderItem.innerHTML = `
                                <div class="reminder-details">
                                    <span>${reminder.time}</span>: ${reminder.message}
                                </div>
                                <div class="reminder-actions">
                                    <button class="edit-reminder-btn"
                                            data-person="${personName}"
                                            data-time="${reminder.time}"
                                            data-message="${reminder.message}">Edit</button>
                                    <button class="delete-reminder-btn"
                                            data-person="${personName}"
                                            data-time="${reminder.time}"
                                            data-message="${reminder.message}">Delete</button>
                                </div>
                            `;
                            remindersListDiv.appendChild(reminderItem);
                        });
                    }
                }
                if (!hasReminders) {
                    remindersListDiv.innerHTML = '<p>No reminders set.</p>';
                }
                attachReminderActionListeners();
            } else {
                remindersListDiv.innerHTML = '<p>No reminders set.</p>';
            }
        } catch (error) {
            console.error('Error loading reminders data:', error);
            remindersListDiv.innerHTML = '<p>Error loading reminders data.</p>';
        }
    }

    function attachReminderActionListeners() {
        // Edit Reminder
        document.querySelectorAll('.edit-reminder-btn').forEach(button => {
            button.addEventListener('click', async (e) => {
                const person = e.target.dataset.person;
                const oldTime = e.target.dataset.time;
                const oldMessage = e.target.dataset.message;

                const newTime = prompt(`Edit time for ${person}'s reminder "${oldMessage}" (Current: ${oldTime}):`, oldTime);
                if (newTime === null) return; // User cancelled

                const newMessage = prompt(`Edit message for ${person}'s reminder at ${newTime} (Current: "${oldMessage}"):`, oldMessage);
                if (newMessage === null) return; // User cancelled

                const formData = new FormData();
                formData.append('person_name', person);
                formData.append('old_time', oldTime);
                formData.append('old_message', oldMessage);
                formData.append('new_time', newTime);
                formData.append('new_message', newMessage);

                try {
                    const response = await fetch('/edit_reminder', {
                        method: 'POST',
                        body: formData,
                    });
                    const data = await response.json();
                    alert(data.message);
                    if (data.success) {
                        loadRemindersData();
                    }
                } catch (error) {
                    console.error('Error editing reminder:', error);
                    alert('An error occurred while editing the reminder.');
                }
            });
        });

        // Delete Reminder
        document.querySelectorAll('.delete-reminder-btn').forEach(button => {
            button.addEventListener('click', async (e) => {
                const person = e.target.dataset.person;
                const time = e.target.dataset.time;
                const message = e.target.dataset.message;

                if (confirm(`Are you sure you want to delete the reminder for ${person} at ${time}: "${message}"?`)) {
                    const formData = new FormData();
                    formData.append('person_name', person);
                    formData.append('time', time);
                    formData.append('message', message);

                    try {
                        const response = await fetch('/delete_reminder', {
                            method: 'POST',
                            body: formData,
                        });
                        const data = await response.json();
                        alert(data.message);
                        if (data.success) {
                            loadRemindersData();
                        }
                    } catch (error) {
                        console.error('Error deleting reminder:', error);
                        alert('An error occurred while deleting the reminder.');
                    }
                }
            });
        });
    }

    // --- Initial Load ---
    populateReminderPersonSelect();
    loadRemindersData();
});