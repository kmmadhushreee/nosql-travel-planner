
// Stress Tracker JS - Enhanced for Visibility

let clickCount = 0;
let startTime = Date.now();
let repeatedSearches = parseInt(sessionStorage.getItem('searchCount') || 0);

// Update Displays
const clickDisplay = document.getElementById('clickDisplay');
const timeDisplay = document.getElementById('timeDisplay');
const searchDisplay = document.getElementById('searchDisplay');

function updateWidget() {
    if (clickDisplay) clickDisplay.innerText = clickCount;
    if (searchDisplay) searchDisplay.innerText = repeatedSearches;
    if (timeDisplay) {
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        timeDisplay.innerText = seconds;
    }
}

// Track Clicks
document.addEventListener('click', () => {
    clickCount++;
    updateWidget();
});

// Update Time every second
setInterval(updateWidget, 1000);

// Track Search Submits
const searchForm = document.getElementById('searchForm');
if (searchForm) {
    searchForm.addEventListener('submit', () => {
        repeatedSearches++;
        sessionStorage.setItem('searchCount', repeatedSearches);
        updateWidget();
    });
}

// Send Data to Backend
function sendStressData() {
    const timeSpent = (Date.now() - startTime) / 1000;

    const daata = {
        click_count: clickCount,
        time_spent_sec: timeSpent,
        repeated_searches_count: repeatedSearches
    };

    // Use sendBeacon for more reliability on unload, fallback to fetch
    const blob = new Blob([JSON.stringify(daata)], { type: 'application/json' });
    navigator.sendBeacon('/api/stress_log', blob);
}

// Send on unload
window.addEventListener('beforeunload', sendStressData);
