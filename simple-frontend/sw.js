const CACHE_NAME = 'v1';
const STATIC_ASSETS = [
    '/static/main.js',
    '/static/styles.css',
    '/index.html'
];

// Service Worker Install
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Error caching static assets:', error);
            })
    );
});

// Service Worker Activate
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        Promise.all([
            clients.claim(),
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cache => {
                        if (cache !== CACHE_NAME) {
                            console.log('Clearing old cache:', cache);
                            return caches.delete(cache);
                        }
                    })
                );
            })
        ])
    );
});

// Fetch handler with API exclusion
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Bypass service worker for non-GET requests and API calls
    if (event.request.method !== 'GET' || url.pathname.startsWith('/votes') || url.pathname.startsWith('/push') || url.pathname.startsWith('/subscribe')) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || fetch(event.request);
        })
    );
});

// Handle push events
self.addEventListener('push', (event) => {
    console.log('Push event received:', event);
    
    try {
        const data = event.data.json();
        console.log('Push data:', data);
        
        // Create notification options based on the vote data
        const options = {
            body: data.notification_body || 'New vote on your post',
            icon: '/static/icon.png',
            badge: '/static/badge.png',
            data: {
                url: '/',  // URL to open when notification is clicked
                postId: data.post_id,
                voterEmail: data.voter_email_id
            },
            requireInteraction: true,
            actions: [
                {
                    action: 'view',
                    title: 'View Post'
                }
            ],
            tag: `vote-${data.post_id}-${Date.now()}`, // Unique tag for each notification
            renotify: true
        };

        event.waitUntil(
            self.registration.showNotification(data.notification_title || 'Vote Notification', options)
                .then(() => console.log('Vote notification shown successfully'))
                .catch(error => console.error('Error showing vote notification:', error))
        );
    } catch (error) {
        console.error('Error processing push event:', error);
        // Show a fallback notification if JSON parsing fails
        event.waitUntil(
            self.registration.showNotification('New Activity', {
                body: 'Someone interacted with your post',
                icon: '/static/icon.png',
                badge: '/static/badge.png'
            })
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    // Handle action clicks
    if (event.action === 'view') {
        // Open the specific post if possible
        const postUrl = event.notification.data?.url || '/';
        event.waitUntil(
            clients.openWindow(postUrl)
                .then(() => console.log('Opened post URL'))
                .catch(error => console.error('Error opening URL:', error))
        );
    } else {
        // Default click behavior
        event.waitUntil(
            clients.openWindow('/')
                .then(() => console.log('Opened main page'))
                .catch(error => console.error('Error opening main page:', error))
        );
    }
});
