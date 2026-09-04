/**
 * SmartCare Queue AI - Interactive Hospital Map & Indoor Wayfinding
 */

let locationsList = [];
let selectedStartId = null;
let selectedEndId = null;
let activeFloor = 'Ground Floor';

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient', 'staff', 'doctor', 'admin'])) return;

  await loadHospitalLocations();
  setupMapControls();
  drawHospitalFloorplan();
});

async function loadHospitalLocations() {
  try {
    const res = await window.api.get('/navigation/locations');
    locationsList = res.data || [];
    populateLocationDropdowns(locationsList);

    // Check if query param specified destination
    const params = new URLSearchParams(window.location.search);
    const destName = params.get('dest');
    if (destName) {
      const match = locationsList.find(l => l.name.toLowerCase().includes(destName.toLowerCase()));
      if (match) {
        selectedEndId = match.id;
        const endSelect = document.getElementById('end-location-select');
        if (endSelect) endSelect.value = match.id;
        calculateAndDisplayRoute();
      }
    }
  } catch (err) {
    console.error('Failed to load hospital locations:', err);
  }
}

function populateLocationDropdowns(locations) {
  const startSelect = document.getElementById('start-location-select');
  const endSelect = document.getElementById('end-location-select');
  if (!startSelect || !endSelect) return;

  const optionsHtml = locations.map(l => `<option value="${l.id}">${l.name} (${l.floor})</option>`).join('');
  
  startSelect.innerHTML = optionsHtml;
  endSelect.innerHTML = optionsHtml;

  // Defaults
  const entrance = locations.find(l => l.location_type === 'entrance') || locations[0];
  const cardio = locations.find(l => l.name.includes('Cardiology')) || locations[1];

  if (entrance) startSelect.value = entrance.id;
  if (cardio) endSelect.value = cardio.id;

  selectedStartId = startSelect.value;
  selectedEndId = endSelect.value;
}

function setupMapControls() {
  const startSelect = document.getElementById('start-location-select');
  const endSelect = document.getElementById('end-location-select');
  const calcBtn = document.getElementById('calculate-route-btn');
  const searchInput = document.getElementById('location-search-input');

  if (startSelect) {
    startSelect.addEventListener('change', (e) => {
      selectedStartId = e.target.value;
      calculateAndDisplayRoute();
    });
  }

  if (endSelect) {
    endSelect.addEventListener('change', (e) => {
      selectedEndId = e.target.value;
      calculateAndDisplayRoute();
    });
  }

  if (calcBtn) {
    calcBtn.addEventListener('click', () => {
      calculateAndDisplayRoute();
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.trim().toLowerCase();
      if (!term) return;
      const found = locationsList.find(l => l.name.toLowerCase().includes(term) || l.description.toLowerCase().includes(term));
      if (found) {
        selectedEndId = found.id;
        if (endSelect) endSelect.value = found.id;
        calculateAndDisplayRoute();
      }
    });
  }
}

function switchFloor(floorName) {
  activeFloor = floorName;
  document.querySelectorAll('.floor-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.floor === floorName);
  });
  calculateAndDisplayRoute();
}
window.switchFloor = switchFloor;

async function calculateAndDisplayRoute() {
  if (!selectedStartId || !selectedEndId) return;

  try {
    const res = await window.api.get(`/navigation/route?from=${selectedStartId}&to=${selectedEndId}`);
    if (res.success && res.data) {
      renderRouteSummary(res.data);
      drawHospitalFloorplan(res.data);
    }
  } catch (err) {
    console.warn('Routing error:', err);
  }
}

function renderRouteSummary(routeData) {
  const container = document.getElementById('route-summary-container');
  if (!container) return;

  container.innerHTML = `
    <div class="route-summary-box">
      <div class="route-summary-header">
        <span>🚶 Estimated Walk: ~${routeData.walking_minutes} min</span>
        <span>${routeData.distance_meters} meters</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">
        From <strong>${routeData.from.name}</strong> to <strong>${routeData.to.name}</strong>
        ${routeData.floor_change ? ' • <span style="color:var(--warning); font-weight:600;">(Change Floor via Lift/Stairs)</span>' : ''}
      </div>
      <ol class="route-steps-list">
        ${routeData.steps.map((step, idx) => `
          <li class="route-step-item">
            <span class="step-num-badge">${idx + 1}</span>
            <span>${step}</span>
          </li>
        `).join('')}
      </ol>
    </div>
  `;
}

function drawHospitalFloorplan(routeData = null) {
  const canvas = document.getElementById('hospital-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  // Set dimensions
  canvas.width = 750;
  canvas.height = 520;

  // Background
  ctx.fillStyle = '#F8FAFC';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Hospital Building Outer Wall
  ctx.strokeStyle = '#CBD5E1';
  ctx.lineWidth = 4;
  ctx.strokeRect(30, 30, canvas.width - 60, canvas.height - 60);

  // Central Corridors
  ctx.fillStyle = '#EFF6FF';
  // Horizontal corridor
  ctx.fillRect(40, 260, canvas.width - 80, 50);
  // Vertical corridor
  ctx.fillRect(350, 40, 50, canvas.height - 80);

  // Corridor boundary lines
  ctx.strokeStyle = '#93C5FD';
  ctx.lineWidth = 1;
  ctx.strokeRect(40, 260, canvas.width - 80, 50);
  ctx.strokeRect(350, 40, 50, canvas.height - 80);

  // Filter locations for active floor
  const floorLocations = locationsList.filter(l => l.floor === activeFloor);

  // Draw Room Nodes
  floorLocations.forEach(loc => {
    const isStart = routeData && routeData.from.id === loc.id;
    const isEnd = routeData && routeData.to.id === loc.id;

    // Room Box
    ctx.fillStyle = isStart ? '#DCFCE7' : (isEnd ? '#FEE2E2' : '#FFFFFF');
    ctx.strokeStyle = isStart ? '#16A34A' : (isEnd ? '#DC2626' : '#94A3B8');
    ctx.lineWidth = (isStart || isEnd) ? 3 : 1.5;

    const w = 110;
    const h = 60;
    const x = loc.x_position - w / 2;
    const y = loc.y_position - h / 2;

    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x, y, w, h);

    // Label
    ctx.fillStyle = isStart ? '#15803D' : (isEnd ? '#B91C1C' : '#1E293B');
    ctx.font = 'bold 11px Poppins, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(loc.name.substring(0, 16), loc.x_position, loc.y_position);

    ctx.fillStyle = '#64748B';
    ctx.font = '9px Poppins, sans-serif';
    ctx.fillText(loc.location_type.toUpperCase(), loc.x_position, loc.y_position + 14);

    // Pin indicator
    if (isStart || isEnd) {
      ctx.fillStyle = isStart ? '#16A34A' : '#DC2626';
      ctx.beginPath();
      ctx.arc(loc.x_position, loc.y_position - 22, 6, 0, Math.PI * 2);
      ctx.fill();
    }
  });

  // Draw Route Path if start and end match current floor
  if (routeData) {
    const fromLoc = routeData.from;
    const toLoc = routeData.to;

    if (fromLoc.floor === activeFloor && toLoc.floor === activeFloor) {
      ctx.beginPath();
      ctx.strokeStyle = '#2563EB';
      ctx.lineWidth = 4;
      ctx.setLineDash([8, 6]);

      ctx.moveTo(fromLoc.x_position, fromLoc.y_position);
      // Waypoint through central corridor junction
      ctx.lineTo(375, fromLoc.y_position);
      ctx.lineTo(375, toLoc.y_position);
      ctx.lineTo(toLoc.x_position, toLoc.y_position);

      ctx.stroke();
      ctx.setLineDash([]); // Reset line dash
    }
  }
}
