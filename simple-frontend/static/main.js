let token = null;
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            const registration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('[SW] Registered with scope:', registration.scope);
            
            // Check if we have an active service worker
            if (registration.active) {
                console.log('[SW] Service Worker is active');
            }
            
            // Check push subscription status
            const subscription = await registration.pushManager.getSubscription();
            console.log('[SW] Push Subscription status:', subscription ? 'Subscribed' : 'Not subscribed');
            
            if (subscription) {
                console.log('[SW] Current subscription:', subscription);
            }
        } catch (error) {
            console.error('[SW] Registration failed:', error);
        }
    });
}


const API_URL = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    return 'https://nsqy7zeyor4pyhqd4gbt4eg2mi0iaehx.lambda-url.us-east-1.on.aws';
})();

const VAPID_PUBLIC_KEY = 'BGrvddJ7X5ycoFZKGRLBKtwQU0SVlv2C8V10ppAzek4_mDvxfWWswb0MSoE-8-4TBfDWl9uH7xJhjd6GEfPHaOo=';

// Initialize Bootstrap Modal
const authModal = new bootstrap.Modal(document.getElementById('authModal'));

// Toggle Auth Forms
document.getElementById('loginBtn').addEventListener('click', () => {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('registerForm').classList.add('hidden');
    authModal.show();
});

document.getElementById('registerBtn').addEventListener('click', () => {
    document.getElementById('registerForm').classList.remove('hidden');
    document.getElementById('loginForm').classList.add('hidden');
    authModal.show();
});

// Register Handler
document.getElementById('registerFormData').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value
    };

    try {
        const res = await fetch(`${API_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            alert('Registered! Please log in.');
            document.getElementById('registerForm').classList.add('hidden');
            document.getElementById('loginForm').classList.remove('hidden');
        } else {
            const err = await res.json();
            alert('Registration failed: ' + (err.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// Login Handler
document.getElementById('loginFormData').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new URLSearchParams();
    formData.append('username', document.getElementById('loginEmail').value);
    formData.append('password', document.getElementById('loginPassword').value);

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            authModal.hide(); // Hide the modal after successful login
            document.getElementById('createPostForm').classList.remove('hidden');
            document.getElementById('notificationPrefs').classList.remove('hidden');
            fetchPosts();
            fetchNotificationPreferences();
        } else {
            const err = await res.json();
            alert('Login failed: ' + (err.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// Create Post
document.getElementById('postFormData').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        title: document.getElementById('postTitle').value,
        content: document.getElementById('postContent').value,
        published: document.getElementById('postPublished').checked,
        rating: document.getElementById('postRating').value || null
    };

    try {
        const res = await fetch(`${API_URL}/posts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            alert('Post created!');
            document.getElementById('postFormData').reset();
            fetchPosts();
        }
    } catch (err) {
        console.error('Post error:', err);
    }
});

// Notification Preferences Handler
document.getElementById('notificationPrefsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        const pushEnabled = document.getElementById('pushEnabled').checked;
        console.log('[Preferences] Push notifications enabled:', pushEnabled);
        
        if (pushEnabled) {
            // Check notification permission
            if (Notification.permission === 'denied') {
                console.log('[Preferences] Notifications are denied');
                alert('Please enable notifications in your browser settings');
                document.getElementById('pushEnabled').checked = false;
                return;
            }
            
            if (Notification.permission === 'default') {
                console.log('[Preferences] Requesting notification permission');
                const permission = await Notification.requestPermission();
                console.log('[Preferences] Permission result:', permission);
                if (permission !== 'granted') {
                    document.getElementById('pushEnabled').checked = false;
                    return;
                }
            }
            
            // Initialize push notifications
            console.log('[Preferences] Initializing push notifications');
            const subscription = await initializePushNotifications();
            console.log('[Preferences] Push subscription:', subscription);
            
            // Test the notification
            await testPushNotification();
        } else {
            // Unsubscribe from push notifications
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                await subscription.unsubscribe();
                console.log('[Preferences] Unsubscribed from push notifications');
            }
        }
        
        // Update preferences on server
        await updateSubscriptionOnServer(pushEnabled ? await (await navigator.serviceWorker.ready).pushManager.getSubscription() : null);
        
        alert('Notification preferences saved successfully');
    } catch (error) {
        console.error('[Preferences] Error:', error);
        alert('Failed to save notification preferences: ' + error.message);
        document.getElementById('pushEnabled').checked = false;
    }
});

// Service Worker Registration
async function registerServiceWorker() {
    try {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            console.log('Registering service worker...');
            const swUrl = document.querySelector('meta[name="service-worker-url"]').content;
            const registration = await navigator.serviceWorker.register(swUrl);
            console.log('Service Worker registered:', registration);
            return registration;
        }
        throw new Error('Service Worker or Push API not supported');
    } catch (error) {
        console.error('Service Worker registration failed:', error);
        throw error;
    }
}

// Initialize Push Notifications
async function initializePushNotifications() {
    try {
        console.log('Initializing push notifications...');
        const registration = await registerServiceWorker();
        
        // Check if already subscribed
        let subscription = await registration.pushManager.getSubscription();
        
        if (!subscription) {
            // Get VAPID key from meta tag
            const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]').content;
            const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
            
            // Subscribe to push notifications
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });
            console.log('Push notification subscription created:', subscription);
        }
        
        // Send subscription to server
        await updateSubscriptionOnServer(subscription);
        return subscription;
    } catch (error) {
        console.error('Push notification initialization failed:', error);
        throw error;
    }
}

// Update subscription on server
async function updateSubscriptionOnServer(subscription) {
    if (!token) {
        console.error('No authentication token available');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/preferences`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                push_enabled: true,
                push_subscription: JSON.stringify(subscription),
                sms_enabled: document.getElementById('smsEnabled').checked,
                webhook_enabled: document.getElementById('webhookEnabled').checked,
                webhook_url: document.getElementById('webhookUrl').value || null,
                phone_number: document.getElementById('phoneNumber').value || null
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to update subscription: ${response.status}`);
        }

        console.log('Subscription updated on server successfully');
    } catch (error) {
        console.error('Failed to update subscription on server:', error);
        throw error;
    }
}

// Function to convert VAPID public key from base64 to Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Function to subscribe to push notifications
async function subscribeUserToPush() {
    try {
        console.log('Checking for existing subscription...');
        const registration = await navigator.serviceWorker.ready;
        let subscription = await registration.pushManager.getSubscription();

        if (!subscription) {
            console.log('No subscription found. Creating new subscription...');
            const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]').content;
            const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
            console.log('Push notification subscription created:', subscription);
        } else {
            console.log('Existing subscription found:', subscription);
        }

        // Send the subscription to your backend
        const response = await fetch(`${API_URL}/api/save-subscription`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                user_id: localStorage.getItem('user_id')
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to save subscription: ${response.status}`);
        }

        const result = await response.json();
        console.log('Subscription saved successfully:', result);
        return subscription;
    } catch (error) {
        console.error('Error subscribing to push notifications:', error);
        throw error;
    }
}

// Function to handle notification preferences
async function handleNotificationPreferences() {
    try {
        console.log('Checking notification permission status...');
        let permission = Notification.permission;

        if (permission === 'default') {
            console.log('Requesting notification permission...');
            permission = await Notification.requestPermission();
        }

        if (permission === 'granted') {
            console.log('Notification permission granted');
            const subscription = await subscribeUserToPush();
            
            // Update UI to show notifications are enabled
            document.getElementById('notification-status').textContent = 'Notifications: Enabled';
            document.getElementById('enable-notifications').style.display = 'none';
            document.getElementById('disable-notifications').style.display = 'block';
            
            return subscription;
        } else {
            console.log('Notification permission denied');
            // Update UI to show notifications are disabled
            document.getElementById('notification-status').textContent = 'Notifications: Disabled';
            document.getElementById('enable-notifications').style.display = 'block';
            document.getElementById('disable-notifications').style.display = 'none';
            
            throw new Error('Notification permission denied');
        }
    } catch (error) {
        console.error('Error handling notification preferences:', error);
        // Show error message to user
        document.getElementById('notification-error').textContent = 
            'Failed to enable notifications. Please try again or check browser settings.';
        throw error;
    }
}

// Event listener for enabling notifications
document.getElementById('enable-notifications').addEventListener('click', async () => {
    try {
        await handleNotificationPreferences();
    } catch (error) {
        console.error('Failed to enable notifications:', error);
    }
});

// Event listener for disabling notifications
document.getElementById('disable-notifications').addEventListener('click', async () => {
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        
        if (subscription) {
            await subscription.unsubscribe();
            console.log('Successfully unsubscribed from push notifications');
            
            // Send unsubscribe request to backend
            const response = await fetch(`${API_URL}/api/remove-subscription`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    user_id: localStorage.getItem('user_id')
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to remove subscription: ${response.status}`);
            }
        }
        
        // Update UI
        document.getElementById('notification-status').textContent = 'Notifications: Disabled';
        document.getElementById('enable-notifications').style.display = 'block';
        document.getElementById('disable-notifications').style.display = 'none';
        document.getElementById('notification-error').textContent = '';
    } catch (error) {
        console.error('Error disabling notifications:', error);
        document.getElementById('notification-error').textContent = 
            'Failed to disable notifications. Please try again.';
    }
});

// Fetch Posts
async function fetchPosts() {
    try {
        const res = await fetch(`${API_URL}/posts`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const posts = await res.json();
        displayPosts(posts);
    } catch (err) {
        console.error('Fetch error:', err);
    }
}

// Display Posts
function displayPosts(posts) {
    const postsContainer = document.getElementById('postsList');
    postsContainer.innerHTML = '';

    posts.forEach(post => {
        const postElement = document.createElement('div');
        postElement.className = 'post-card';
        postElement.innerHTML = `
            <h3>${post.Post.title}</h3>
            <p>${post.Post.content}</p>
            <div class="d-flex align-items-center">
                <span class="me-3">Votes: ${post.votes}</span>
                <button onclick="handleVote(${post.Post.id}, 1)" class="btn btn-sm btn-success me-2" title="Upvote">
                    <i class="fas fa-thumbs-up"></i> Upvote
                </button>
                <button onclick="handleVote(${post.Post.id}, 0)" class="btn btn-sm btn-danger" title="Remove Vote">
                    <i class="fas fa-thumbs-down"></i> Remove Vote
                </button>
            </div>
            <small class="text-muted">Posted by: ${post.Post.owner.email}</small>
        `;
        postsContainer.appendChild(postElement);
    });
}

// Vote Handler
async function handleVote(postId, direction) {
    try {
        console.log(`Attempting to vote on post ${postId} with direction ${direction}`);
        
        const response = await fetch(`${API_URL}/votes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                post_id: postId,
                dir: direction
            })
        });

        const responseData = await response.json();
        console.log('Vote response:', responseData);

        if (response.ok) {
            console.log('Vote successful:', responseData.message);
            
            // Check if push notification was triggered
            if (responseData.notification_sent) {
                console.log('Push notification was triggered by the server');
            } else {
                console.log('No push notification was triggered by the server');
            }
            
            // Check service worker status
            const swRegistration = await navigator.serviceWorker.ready;
            console.log('Service Worker Registration Status:', swRegistration.active ? 'Active' : 'Inactive');
            
            // Check push subscription status
            const pushSubscription = await swRegistration.pushManager.getSubscription();
            console.log('Push Subscription Status:', pushSubscription ? 'Subscribed' : 'Not Subscribed');
            
            if (pushSubscription) {
                console.log('Current Push Subscription:', pushSubscription);
            }
            
            fetchPosts();  // Refresh posts after voting
        } else {
            // If vote doesn't exist for downvote, try upvoting first
            if (direction === 0 && response.status === 404) {
                console.log('No vote found to remove. User needs to upvote first.');
                alert('You need to upvote first before you can remove your vote.');
            } else {
                console.error('Vote failed:', responseData);
                alert(responseData.detail || 'Failed to process vote');
            }
        }
    } catch (error) {
        console.error('Vote error:', error);
        alert('Error processing vote: ' + error.message);
    }
}

// Fetch Preferences
async function fetchNotificationPreferences() {
    try {
        const res = await fetch(`${API_URL}/preferences`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const prefs = await res.json();
            document.getElementById('smsEnabled').checked = !!prefs.sms_enabled;
            document.getElementById('webhookEnabled').checked = !!prefs.webhook_enabled;
            document.getElementById('webhookUrl').value = prefs.webhook_url || '';
            document.getElementById('phoneNumber').value = prefs.phone_number || '';
            document.getElementById('pushEnabled').checked = !!prefs.push_enabled;
        }
    } catch (err) {
        console.error('Prefs error:', err);
    }
}

// Add this function after your existing code
async function testPushNotification() {
    try {
        // Get the current registration
        const registration = await navigator.serviceWorker.ready;
        console.log('[Test] Service Worker Registration:', registration);

        // Get the push subscription
        const subscription = await registration.pushManager.getSubscription();
        console.log('[Test] Current Push Subscription:', subscription);

        if (!subscription) {
            console.log('[Test] No subscription found. Creating new subscription...');
            const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]').content;
            const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
            
            const newSubscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
            console.log('[Test] New subscription created:', newSubscription);
            
            // Send the new subscription to the server
            await updateSubscriptionOnServer(newSubscription);
        }

        // Test the subscription by sending a test notification
        const response = await fetch(`${API_URL}/test-notification`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                test_message: 'This is a test notification'
            })
        });

        const result = await response.json();
        console.log('[Test] Test notification response:', result);
    } catch (error) {
        console.error('[Test] Error testing push notification:', error);
    }
}
