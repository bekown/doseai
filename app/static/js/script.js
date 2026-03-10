// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    
    // Read the globals exposed by layout.html
    const serverData = window.serverData || {};
    const injectedData = serverData.global_countdown || null;
    const missedDoseGuidance = serverData.missed_dose_guidance || null;
    const dailyVitalsData = serverData.daily_data_vitals || null;
    const endpoints = serverData.api_endpoints || {};
    const isLoggedIn = serverData.user_authenticated || false;// Read the globals exposed by layout.html
    const serverData = window.serverData || {};
    const injectedData = serverData.global_countdown || null;
    const missedDoseGuidance = serverData.missed_dose_guidance || null;
    const dailyVitalsData = serverData.daily_data_vitals || null;
    const endpoints = serverData.api_endpoints || {};
    const isLoggedIn = serverData.user_authenticated || false;

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // ---  Navigation Link Handling (Smooth Scroll) ---
    // Select all links that contain a hash (#)
    const navLinks = document.querySelectorAll('a[href*="#"]');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Separate the path (e.g., "/home") from the hash (e.g., "#about")
            // If href is just "#about", path is empty string
            const hashIndex = href.indexOf('#');
            
            // If no hash found, ignore
            if (hashIndex === -1) return;

            const targetHash = href.substring(hashIndex); // e.g., "#about"
            const targetPath = href.substring(0, hashIndex); // e.g., "/home" or ""

            // Get current path (normalized to remove trailing slash if present)
            const currentPath = window.location.pathname.replace(/\/$/, "") || "/";
            const cleanTargetPath = targetPath.replace(/\/$/, "") || "/";

            // LOGIC: If the link path matches the current page (or is just a hash), scroll smoothly.
            // We interpret empty targetPath (just "#") as matching current page.
            if (targetPath === "" || cleanTargetPath === currentPath || (currentPath === "/home" && cleanTargetPath === "/")) {
                
                const targetElement = document.querySelector(targetHash);

                if (targetElement) {
                    // Prevent default browser jump/reload
                    e.preventDefault();
                    
                    // Smooth Scroll
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });

                    // Update URL hash without jumping (optional, keeps history clean)
                    history.pushState(null, null, targetHash);
                    
                }
            } else {
                // ELSE: We are on a different page (e.g., Dashboard).
                return;
            }
             
            
        });
    });

    
    /// --- Countdown Logic ---
    // Get the countdown display element
    const countdownElement = document.getElementById('global-countdown-timer');
    const countdownContainer = document.getElementById('global-countdown-container');
    // Get the instance reference we stored on the window object in layout.html
    const doseModalInstance = window.doseModalInstance || null; 
    
    // Get the modal message element to update it
    const doseMessageElement = document.getElementById('dose-alert-message');
    const missedDoseGuidanceElement = document.getElementById('missed-dose-guidance');
    const skipDoseBtn = document.getElementById('skip-dose-button');
    const takeDoseBtn = document.getElementById('take-dose-button');
    const snoozeDoseBtn = document.getElementById('snooze-button');
    const ALERT_AUDIO_SRC = '/static/audio/alert.mp3';

    if (!countdownElement) return;
    
    if (injectedData === null) {
        countdownContainer.style.display = 'none';  
    }

    // --- State Variables ---
    let targetTime = null;
    let currentMedicationId = null;
    let currentMedicationName = null;
    let intervalId = null;
    const SNOOZE_MINUTES = 10;

    // Helper to determine if we are logged in (to prevent running logic unnecessarily)
    const isLoggedIn = !!document.getElementById('global-countdown-container');


    function formatDuration(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    function showModal() {
        console.log('showModal called');
        if (!isLoggedIn || !doseModalInstance) return;

        // 1. Update modal text before showing
        if (doseMessageElement) {
            doseMessageElement.textContent = `Time to take your: ${currentMedicationName || 'medication'}`;
        }
        if (missedDoseGuidanceElement && missedDoseGuidance) {
            if (missedDoseGuidance === null) {
                missedDoseGuidanceElement.textContent = '';
            } else {
                missedDoseGuidanceElement.innerHTML = DOMPurify.sanitize(missedDoseGuidance);
            }
        }
        
        // 2. Use Materialize API to open the modal
        doseModalInstance.open();
    }
    
    function hideModal() { 
        if (!isLoggedIn || !doseModalInstance) return;
        // This is primarily for explicit control, but buttons use `modal-close`
        doseModalInstance.close();
    }
    
    function playAlertSound() {
        // Implementation for playing a sound (using Tone.js or a standard Audio element)
        // Ensure this logic is handled in your environment; 
        // for now, we'll keep it as a placeholder to prevent errors.
        console.log("Playing dose alert sound...");
    }

    function updateCountdown() {
        if (!targetTime) {
            countdownElement.textContent = 'No Upcoming Dose';
            if (intervalId) clearInterval(intervalId);
            intervalId = null;
            return;
        }   
        const now = new Date();
        const distance = targetTime - now;

        if (distance <= 0) {
            countdownElement.textContent = `OVERDUE: ${currentMedicationName}!`;
            clearInterval(intervalId);
            intervalId = null; // Stop timer
            showModal(); // <-- THIS IS THE CRITICAL CALL TO OPEN THE MODAL
            playAlertSound();
            return;
        }
        countdownElement.textContent = `Next Dose: ${formatDuration(distance)}`;
        
        
    }

    function startInterval() {
        if (intervalId) clearInterval(intervalId);
        intervalId = null;        
        updateCountdown(); 
        if (targetTime) {
            intervalId = setInterval(updateCountdown, 1000);            
        }
    }

    /**
     * Central function to update client state based on server response.
     */
    function updateGlobalCountdown(countdownData) {
        if (countdownData && countdownData.next_dose_time) {
            // targetTime needs to be a Date object for comparison logic to work correctly
            targetTime = new Date(countdownData.next_dose_time);
            currentMedicationId = countdownData.medication_id;
            currentMedicationName = countdownData.medication_name;
        } else {
            // No more doses scheduled
            targetTime = null;
            currentMedicationId = null;
            currentMedicationName = null;
        }
        // Restart the timer with the new data
        startInterval();
    }
    
    // --- Event Listeners ---
    
    // We attach listeners to the buttons, which also close the modal due to `modal-close` class.
    
    if (snoozeDoseBtn && isLoggedIn) {
        snoozeDoseBtn.addEventListener('click', async function(e) {
            // Modal closes automatically because the button has `modal-close` class.

            if (!currentMedicationId) return;

            countdownElement.textContent = "Snoozing..."; 
            
            if (endpoints.snooze_dose) {
                try {
                    const response = await fetch(endpoints.snooze_dose, {
                        method: 'POST',
                        credentials: 'same-origin',
                        
                        headers: { 'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                         },
                        body: JSON.stringify({ 
                            medication_id: currentMedicationId,
                            snooze_minutes: SNOOZE_MINUTES 
                        })
                    });
                    if (response.ok) {
                        const data = await response.json();
                        // Handle the new global_countdown object
                        updateGlobalCountdown(data.global_countdown);
                    } else {
                        console.error('Snooze request failed:', response.statusText);
                        M.toast({html: 'Snooze failed. Server error.', classes: 'red darken-2'});
                    }
                } catch (e) {
                    console.error('Error during snooze request:', e);
                    M.toast({html: 'Snooze failed. Network error.', classes: 'red darken-2'});
                }
            }
        });
    }
    
    if (takeDoseBtn && isLoggedIn) {
        takeDoseBtn.addEventListener('click', async function(e) {
            // Modal closes automatically because the button has `modal-close` class.

            if (!currentMedicationId) return;

            countdownElement.textContent = "Recording dose...";
            
            if (endpoints.take_dose) {
                try {
                    const response = await fetch(endpoints.take_dose, {
                        method: 'POST',
                        credentials: 'same-origin',
                        
                        headers: { 'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                         },
                        body: JSON.stringify({ 
                            medication_id: currentMedicationId,
                            taken_at: new Date().toISOString() 
                        })
                    });
                    if (response.ok) {
                        const data = await response.json();
                        M.toast({html: `Dose of ${currentMedicationName} recorded!`, classes: 'green darken-1'});
                        // Handle the new global_countdown object
                        updateGlobalCountdown(data.global_countdown);
                    } else {
                        console.warn('Record dose failed:', response.statusText);
                        M.toast({html: 'Failed to record dose. Server error.', classes: 'red darken-2'});
                    }
                } catch (e) {
                    console.error('Record dose error:', e);
                    M.toast({html: 'Failed to record dose. Network error.', classes: 'red darken-2'});
                }
            }
        });
    }
    if (skipDoseBtn && isLoggedIn) {
        skipDoseBtn.addEventListener('click', async function(e) {
            // Modal closes automatically because the button has `modal-close` class.

            if (!currentMedicationId) return;

            countdownElement.textContent = "Skipping dose...";
            
            if (endpoints.skip_dose) {
                try {
                    const response = await fetch(endpoints.skip_dose, {
                        method: 'POST',
                        credentials: 'same-origin',
                        
                        headers: { 'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                         },
                        body: JSON.stringify({ 
                            medication_id: currentMedicationId
                        })
                    });
                    if (response.ok) {
                        const data = await response.json();
                        M.toast({html: `Dose of ${currentMedicationName} skipped.`, classes: 'orange darken-1'});
                        // Handle the new global_countdown object
                        updateGlobalCountdown(data.global_countdown);
                    } else {
                        console.warn('Skip dose failed:', response.statusText);
                        M.toast({html: 'Failed to skip dose. Server error.', classes: 'red darken-2'});
                    }
                } catch (e) {
                    console.error('Skip dose error:', e);
                    M.toast({html: 'Failed to skip dose. Network error.', classes: 'red darken-2'});
                }
            }
        });
    }

    // Initialize countdown on page load
    if (isLoggedIn) {
        updateGlobalCountdown(injectedData);
    }
    

    // Daily Check-in Modal Logic 
    if (isLoggedIn && dailyVitalsData) {        
        // Get the symptoms container (still dynamic)
        const symptomsformContainer = document.getElementById('symptom-form');
        
        // Add Symptom button handler
        const addSymptomBtn = document.getElementById('add-symptom-btn');
        
        // Symptom counter
        let symptomCounter = 0;
        
        /** Check if user has already submitted today */
        function checkSubmissionStatus() {
            // Hide/show content based on submission status
            const vitalsTab = document.getElementById('vitals-tab');
            const symptomsTab = document.getElementById('symptoms-tab');
            const moodTab = document.getElementById('mood-tab');
            
            if (dailyVitalsData.submitted_today) {
                // Vitals submitted
                if (dailyVitalsData.vitals_submitted && vitalsTab) {
                    vitalsTab.innerHTML = `
                        <div class="col s12">
                            <div class="card-panel green lighten-1 white-text">
                                <i class="material-icons large">check_circle</i>
                                <h5>Vitals Already Submitted</h5>
                                <p>You have already submitted your vitals for today. Thank you!</p>
                                <p class="small">Please head to evaluations section to log new vitals.</p>
                            </div>
                        </div>
                    `;
                }
                
                // Symptoms submitted
                if (dailyVitalsData.symptoms_submitted && symptomsTab) {
                    symptomsTab.innerHTML = `
                        <div class="col s12">
                            <div class="card-panel green lighten-1 white-text">
                                <i class="material-icons large">check_circle</i>
                                <h5>Symptoms Already Submitted</h5>
                                <p>You have already submitted your symptoms for today. Thank you!</p>
                                <p class="small">Please head to evaluations section to log new symptoms.</p>
                            </div>
                        </div>
                    `;
                }
                
                // Mood submitted
                if (dailyVitalsData.mood_submitted && moodTab) {
                    moodTab.innerHTML = `
                        <div class="col s12">
                            <div class="card-panel green lighten-1 white-text">
                                <i class="material-icons large">check_circle</i>
                                <h5>Mood Already Submitted</h5>
                                <p>You have already submitted your mood for today. Thank you!</p>
                            </div>
                        </div>
                    `;
                }
                
                // Hide add symptom button if symptoms submitted
                if (addSymptomBtn && dailyVitalsData.symptoms_submitted) {
                    addSymptomBtn.style.display = 'none';
                }
            } else {
                // No submissions yet - ensure add symptom button is visible
                if (addSymptomBtn) {
                    addSymptomBtn.style.display = 'inline-block';
                }
                
                // Add initial symptom field if container exists
                if (symptomsformContainer && symptomCounter === 0) {
                    addSymptomField();
                }
            }
        }
        
        // Check submission status on load
        checkSubmissionStatus();
        
        // Also check when modal opens
        const checkinModalInstance = M.Modal.getInstance(document.getElementById('daily-checkin-modal'));
        if (checkinModalInstance) {
            const originalOpenStart = checkinModalInstance.options.onOpenStart;
            
            checkinModalInstance.options.onOpenStart = () => {
                if (originalOpenStart) originalOpenStart();
                checkSubmissionStatus();
                
                const overlay = document.querySelector('.modal-overlay');
                if (overlay) overlay.classList.add('glass-picker-modal');
            };
        }

        function addSymptomField() {
            if (!symptomsformContainer) return;
            
            const sfieldGroup = document.createElement('div');
            sfieldGroup.className = 'symptom-field-group row';
            sfieldGroup.dataset.index = symptomCounter;
            
            sfieldGroup.innerHTML = `
                <div class="input-field col s12 m6">
                    <input type="text" id="symptom-${symptomCounter}" name="symptom${symptomCounter}" required>
                    <label for="symptom-${symptomCounter}">Symptom</label>
                </div>
                <div class="input-field col s12 m6">
                    <input type="number" id="duration-${symptomCounter}" name="duration${symptomCounter}" required min="1">
                    <label for="duration-${symptomCounter}">Duration (days)</label>
                </div>
                <div class="input-field col s12 m6">
                    <select id="severity-${symptomCounter}" name="severity${symptomCounter}" required class="browser-default">
                        <option value="" disabled selected>Choose Severity</option>
                        <option value="severe">Severe</option>
                        <option value="moderate">Moderate</option>
                        <option value="mild">Mild</option>
                    </select>
                </div>
                <div class="input-field col s12 m6">
                    <select id="status-${symptomCounter}" name="status${symptomCounter}" required class="browser-default">
                        <option value="" disabled selected>Choose Status</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                    </select>
                </div>
                <div class="col s12 right-align">
                    ${symptomCounter > 0 ? `<button type="button" class="btn-flat red-text remove-symptom-btn" data-index="${symptomCounter}">
                        <i class="material-icons left">remove_circle</i>Remove
                    </button>` : ''}
                </div>
                <div class="col s12"><div class="divider" style="margin: 15px 0;"></div></div>
            `;
            
            symptomsformContainer.appendChild(sfieldGroup);
            
            // Initialize Materialize select elements
            const severitySelect = sfieldGroup.querySelector(`#severity-${symptomCounter}`);
            const statusSelect = sfieldGroup.querySelector(`#status-${symptomCounter}`);
            if (severitySelect) M.FormSelect.init(severitySelect);
            if (statusSelect) M.FormSelect.init(statusSelect);
            M.updateTextFields();
            
            // Add event listener for remove button
            if (symptomCounter > 0) {
                const removeBtn = sfieldGroup.querySelector('.remove-symptom-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', function() {
                        sfieldGroup.remove();
                    });
                }
            }
            
            symptomCounter++;
        }
        
        // Add symptom button logic
        if (addSymptomBtn) {
            addSymptomBtn.addEventListener('click', function(e) {
                e.preventDefault();
                addSymptomField();
            });
        }
        
        // Make the submit function globally accessible
        window.submitDailyCheckin = function() {
            // Check if already submitted
            if (dailyVitalsData.submitted_today) {
                M.toast({html: 'You have already submitted your check-in for today.', classes: 'orange'});
                return;
            }
            
            // Collect data from all forms
            const data = {
                symptoms_count: symptomCounter
            };
            
            // Collect vitals data from static form
            const heartRate = document.getElementById('heart_rate');
            const bpSys = document.getElementById('blood_pressure_systolic');
            const bpDia = document.getElementById('blood_pressure_diastolic');
            const temp = document.getElementById('temperature');
            const respRate = document.getElementById('respiratory_rate');
            
            if (heartRate && heartRate.value) data.heart_rate = heartRate.value;
            if (bpSys && bpSys.value) data.blood_pressure_systolic = bpSys.value;
            if (bpDia && bpDia.value) data.blood_pressure_diastolic = bpDia.value;
            if (temp && temp.value) data.temperature = temp.value;
            if (respRate && respRate.value) data.respiratory_rate = respRate.value;
            
            // Collect symptom data
            data.symptoms = [];
            for (let i = 0; i < symptomCounter; i++) {
                const symptomField = document.getElementById(`symptom-${i}`);
                const durationField = document.getElementById(`duration-${i}`);
                const severityField = document.getElementById(`severity-${i}`);
                const statusField = document.getElementById(`status-${i}`);
                
                if (symptomField && durationField && severityField && statusField) {
                    data.symptoms.push({
                        symptom_name: symptomField.value,
                        duration: durationField.value,
                        severity: severityField.value,
                        status: statusField.value
                    });
                }
            }
            
            // Collect mood data from static form
            const moodRadio = document.querySelector('input[name="mood"]:checked');
            if (moodRadio) data.mood = moodRadio.value;
            
            const moodNotes = document.getElementById('mood_notes');
            if (moodNotes && moodNotes.value) data.mood_notes = moodNotes.value;
            
            console.log('Submitting data:', data);
            
            // Submit to server
            fetch('/daily_checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(responseData => {
                console.log('Response data:', responseData);
                if (responseData.success) {
                    M.toast({html: 'Check-in submitted successfully!', classes: 'green'});
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    M.toast({html: 'Error: ' + responseData.message, classes: 'red'});
                }
            })
            .catch(error => {
                console.error('Error:', error);
                M.toast({html: 'Error: ' + error.message, classes: 'red'});
            });
        };
}
    
    // Notification center
    const notificationTrigger = document.getElementById('notification-trigger');
    const notificationCenter = document.getElementById('notification-center');
    const closeNotification = document.getElementById('close-notification');
    const notificationContent = document.getElementById('notification-content');
    
    if (notificationTrigger && notificationCenter) {
        // Toggle notification center
        notificationTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            notificationCenter.classList.toggle('active');
            
            if (notificationCenter.classList.contains('active')) {
                loadNotifications();
            }
        });
        
        // Close notification center
        if (closeNotification) {
            closeNotification.addEventListener('click', function(e) {
                e.preventDefault();
                notificationCenter.classList.remove('active');
            });
        }
        
        // Close notification center when clicking outside
        document.addEventListener('click', function(e) {
            if (!notificationCenter.contains(e.target) && 
                !notificationTrigger.contains(e.target) && 
                notificationCenter.classList.contains('active')) {
                notificationCenter.classList.remove('active');
            }
        });
    }
    
    // Load notifications from server
    function loadNotifications() {
        if (!notificationContent) return;
        
        notificationContent.innerHTML = '<p class="grey-text center-align">Loading notifications...</p>';
        
        fetch('/api/notifications?limit=10')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.notifications.length > 0) {
                    let html = '';
                    
                    data.notifications.forEach(notification => {
                        const isUnread = !notification.is_read;
                        const badgeClass = isUnread ? 'new' : '';
                        const readClass = isUnread ? '' : 'read';
                        
                        html += `
                        <div class="notification-item ${readClass} ${badgeClass}" data-id="${notification.id}">
                            <div class="notification-header">
                                <span class="notification-title">${DOMPurify.sanitize(notification.title)}</span>
                                <span class="notification-time">${DOMPurify.sanitize(notification.created_at_relative || notification.created_at_formatted || '')}</span>
                            </div>
                            <div class="notification-message">${DOMPurify.sanitize(notification.message)}</div>
                            <div class="notification-actions">
                                ${notification.action_url ? `<a href="${DOMPurify.sanitize(notification.action_url)}" class="btn-flat btn-small">View</a>` : ''}
                                <a href="#!" class="mark-read-btn btn-flat btn-small" data-id="${notification.id}">Mark as read</a>
                                <a href="#!" class="delete-notification-btn btn-flat btn-small red-text" data-id="${notification.id}">Delete</a>
                            </div>
                        </div>
                        `;
                    });
                    
                    // Add mark all as read button
                    html += `
                    <div class="notification-actions-center">
                        <a href="#!" id="mark-all-read-btn" class="btn waves-effect waves-light green darken-2">Mark all as read</a>
                        <a href="#!" id="load-more-btn" class="btn-flat">Load more</a>
                    </div>
                    `;
                    
                    notificationContent.innerHTML = html;
                    
                    // Add event listeners to action buttons
                    addNotificationEventListeners();
                    
                } else {
                    notificationContent.innerHTML = '<p class="grey-text center-align">No notifications</p>';
                }
            })
            .catch(error => {
                console.error('Error loading notifications:', error);
                notificationContent.innerHTML = '<p class="red-text center-align">Error loading notifications</p>';
            });
    }
    
    // Add event listeners to notification action buttons
    function addNotificationEventListeners() {
        // Mark as read buttons
        document.querySelectorAll('.mark-read-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.getAttribute('data-id');
                markNotificationAsRead(notificationId);
            });
        });
        
        // Delete notification buttons
        document.querySelectorAll('.delete-notification-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.getAttribute('data-id');
                deleteNotification(notificationId);
            });
        });
        
        // Mark all as read button
        const markAllBtn = document.getElementById('mark-all-read-btn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                markAllNotificationsAsRead();
            });
        }
        
        // Load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function(e) {
                e.preventDefault();
                // Implement load more functionality
            });
        }
    }
    
    // Mark notification as read
    function markNotificationAsRead(notificationId) {
        fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('new');
                    notificationItem.classList.add('read');
                    
                    // Remove mark as read button
                    const markReadBtn = notificationItem.querySelector('.mark-read-btn');
                    if (markReadBtn) {
                        markReadBtn.remove();
                    }
                }
                
                // Update badge count
                updateNotificationBadge(data.unread_count);
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }
    
    // Mark all notifications as read
    function markAllNotificationsAsRead() {
        fetch('/api/notifications/read-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all notifications UI
                document.querySelectorAll('.notification-item').forEach(item => {
                    item.classList.remove('new');
                    item.classList.add('read');
                    
                    // Remove mark as read buttons
                    const markReadBtn = item.querySelector('.mark-read-btn');
                    if (markReadBtn) {
                        markReadBtn.remove();
                    }
                });
                
                // Update badge count to 0
                updateNotificationBadge(0);
            }
        })
        .catch(error => console.error('Error marking all notifications as read:', error));
    }
    
    // Delete notification
    function deleteNotification(notificationId) {
        fetch(`/api/notifications/${notificationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove notification from UI
                const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.remove();
                }
                
                // Update badge count
                updateNotificationBadge(data.unread_count);
                
                // If no notifications left, show message
                if (document.querySelectorAll('.notification-item').length === 0) {
                    notificationContent.innerHTML = '<p class="grey-text center-align">No notifications</p>';
                }
            }
        })
        .catch(error => console.error('Error deleting notification:', error));
    }
    
    // Update notification badge count
    function updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        
        if (count > 0) {
            if (badge) {
                badge.textContent = count;
                badge.style.display = 'inline';
            } else {
                // Create badge if it doesn't exist
                const newBadge = document.createElement('span');
                newBadge.id = 'notification-badge';
                newBadge.className = 'notification-badge';
                newBadge.textContent = count;
                newBadge.style.display = 'inline';
                
                const icon = notificationTrigger.querySelector('i');
                if (icon) {
                    icon.parentNode.insertBefore(newBadge, icon.nextSibling);
                }
            }
        } else {
            if (badge) {
                badge.style.display = 'none';
            }
        }
    }
    
    // Auto-generate notifications periodically (every 5 minutes)
    if (sessionStorage.getItem('user_id')) {
        // Check for new notifications every 5 minutes
        setInterval(() => {
            fetch('/api/notifications/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.unread_count > 0) {
                    // Update badge count
                    updateNotificationBadge(data.unread_count);
                    
                    // Show toast notification if new notifications were generated
                    if (data.total_generated > 0) {
                        M.toast({
                            html: `You have ${data.unread_count} new notification${data.unread_count > 1 ? 's' : ''}`,
                            classes: 'rounded'
                        });
                    }
                }
            })
            .catch(error => console.error('Error generating notifications:', error));
        }, 300000); // 5 minutes
        
        // Also generate notifications immediately on page load
        fetch('/api/notifications/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.unread_count > 0) {
                updateNotificationBadge(data.unread_count);
            }
        })
        .catch(error => console.error('Error generating notifications on load:', error));
    }
});