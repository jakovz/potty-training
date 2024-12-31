let chart;
const UPDATE_INTERVAL = 60000; // Update every minute

function initChart(data) {
    const ctx = document.getElementById('eventChart').getContext('2d');
    
    const datasets = processDataForChart(data);
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Average Time Between Events (hours)'
                    }
                }
            }
        }
    });
}

function processDataForChart(data) {
    const datasets = [];
    const groupedData = {};

    data.forEach(entry => {
        const key = `${entry.type}-${entry.location}`;
        if (!groupedData[key]) {
            groupedData[key] = [];
        }
        groupedData[key].push({
            x: new Date(entry.day),
            y: entry.avg_time_between
        });
    });

    Object.entries(groupedData).forEach(([key, values]) => {
        const [type, location] = key.split('-');
        datasets.push({
            label: `${type} - ${location}`,
            data: values,
            fill: false,
            borderColor: getRandomColor()
        });
    });

    return datasets;
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

async function loadData() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (chart) {
            chart.destroy();
        }
        initChart(data);
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Add auto-update functionality
function startAutoUpdate() {
    loadData(); // Initial load
    setInterval(loadData, UPDATE_INTERVAL);
}

document.getElementById('eventForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const date = document.getElementById('date').value;
    const hours = document.getElementById('hours').value.padStart(2, '0');
    const minutes = document.getElementById('minutes').value.padStart(2, '0');
    
    const formData = {
        type: document.getElementById('type').value,
        location: document.getElementById('location').value,
        timestamp: `${date}T${hours}:${minutes}`
    };

    try {
        await fetch('/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        await loadData();
    } catch (error) {
        console.error('Error saving event:', error);
    }
});

// Handle the "Now" button
document.getElementById('setNowButton').addEventListener('click', () => {
    const now = new Date();
    document.getElementById('date').valueAsDate = now;
    document.getElementById('hours').value = now.getHours().toString().padStart(2, '0');
    document.getElementById('minutes').value = now.getMinutes().toString().padStart(2, '0');
});

// Replace the DOMContentLoaded event listener with startAutoUpdate
document.addEventListener('DOMContentLoaded', startAutoUpdate);

// Add this after your existing event listeners
document.querySelectorAll('.select-button').forEach(button => {
    button.addEventListener('click', () => {
        const target = button.dataset.target;
        const value = button.dataset.value;
        
        // Update hidden input
        document.getElementById(target).value = value;
        
        // Update button styles
        document.querySelectorAll(`.select-button[data-target="${target}"]`)
            .forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    });
}); 