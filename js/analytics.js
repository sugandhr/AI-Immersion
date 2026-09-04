/**
 * SmartCare Queue AI - Operational Analytics & AI Insights Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['staff', 'admin', 'doctor'])) return;

  await loadAnalyticsDashboard();
});

async function loadAnalyticsDashboard() {
  try {
    const [metricsRes, insightsRes] = await Promise.all([
      window.api.get('/analytics/dashboard'),
      window.api.get('/analytics/ai-insights')
    ]);

    const metrics = metricsRes.data || {};
    const insights = insightsRes.data || [];

    // KPI Cards
    const totalTodayEl = document.getElementById('analytics-total-today');
    const avgWaitEl = document.getElementById('analytics-avg-wait');
    const servedEl = document.getElementById('analytics-total-served');
    const satisfactionEl = document.getElementById('analytics-satisfaction');

    if (totalTodayEl) totalTodayEl.textContent = metrics.total_patients_today || 0;
    if (avgWaitEl) avgWaitEl.textContent = `${metrics.average_wait_minutes || 18} min`;
    if (servedEl) servedEl.textContent = metrics.completed_patients || 0;
    if (satisfactionEl) satisfactionEl.textContent = `${metrics.satisfaction_rate || 4.8} / 5.0`;

    // Draw Pure HTML5 Canvas Charts
    drawPeakHoursChart('peak-hours-canvas', metrics.hourly_traffic || []);
    drawDepartmentChart('dept-distribution-canvas', metrics.department_breakdown || []);

    // Render AI Operational Insights
    renderAIInsights(insights);
  } catch (err) {
    window.api.showToast('Failed to load analytics: ' + err.message, 'danger');
  }
}

function drawPeakHoursChart(canvasId, trafficData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 540;
  canvas.height = 260;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const padding = 40;
  const chartW = canvas.width - padding * 2;
  const chartH = canvas.height - padding * 2;

  const maxVal = Math.max(...trafficData.map(d => d.patients), 60);

  // Axes
  ctx.strokeStyle = '#E2E8F0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, canvas.height - padding);
  ctx.lineTo(canvas.width - padding, canvas.height - padding);
  ctx.stroke();

  // Draw Bars
  const barW = chartW / trafficData.length - 12;
  trafficData.forEach((d, i) => {
    const x = padding + i * (barW + 12) + 6;
    const barH = (d.patients / maxVal) * chartH;
    const y = canvas.height - padding - barH;

    // Gradient bar
    const grad = ctx.createLinearGradient(0, y, 0, canvas.height - padding);
    grad.addColorStop(0, '#2563EB');
    grad.addColorStop(1, '#06B6D4');

    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barW, barH);

    // Label
    ctx.fillStyle = '#64748B';
    ctx.font = '10px Poppins, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(d.hour, x + barW / 2, canvas.height - padding + 16);

    // Value
    ctx.fillStyle = '#1E293B';
    ctx.font = 'bold 10px Poppins, sans-serif';
    ctx.fillText(d.patients, x + barW / 2, y - 6);
  });
}

function drawDepartmentChart(canvasId, deptData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 540;
  canvas.height = 260;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const padding = 30;
  const startX = padding;
  const barHeight = 24;
  const gap = 14;

  const maxVal = Math.max(...deptData.map(d => d.count), 20);

  deptData.slice(0, 5).forEach((dept, i) => {
    const y = padding + i * (barHeight + gap);
    const availableW = canvas.width - padding * 2 - 140;
    const w = (dept.count / maxVal) * availableW;

    // Dept name
    ctx.fillStyle = '#1E293B';
    ctx.font = 'bold 11px Poppins, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(dept.name, startX, y + 16);

    // Bar background
    ctx.fillStyle = '#F1F5F9';
    ctx.fillRect(startX + 130, y, availableW, barHeight);

    // Value bar
    ctx.fillStyle = '#2563EB';
    ctx.fillRect(startX + 130, y, w, barHeight);

    // Count
    ctx.fillStyle = '#64748B';
    ctx.font = 'bold 11px Poppins, sans-serif';
    ctx.fillText(`${dept.count} patients`, startX + 140 + w, y + 16);
  });
}

function renderAIInsights(insights) {
  const container = document.getElementById('ai-insights-container');
  if (!container) return;

  container.innerHTML = insights.map(item => `
    <div class="ai-insight-card severity-${item.severity}">
      <div class="insight-header">
        <span class="insight-dept">${item.department}</span>
        <span class="badge badge-${item.severity === 'high' ? 'danger' : (item.severity === 'medium' ? 'warning' : 'success')}">
          ${item.severity.toUpperCase()} LOAD
        </span>
      </div>
      <p style="font-size: 0.88rem; color: var(--text-main); margin-bottom: 0.5rem;">
        ${item.insight}
      </p>
      <div style="font-size: 0.82rem; color: var(--text-muted);">
        Peak Window: <strong>${item.peak_period}</strong> • Avg Wait: <strong>${item.average_wait}</strong>
      </div>
      <div class="insight-suggestion">
        💡 <strong>AI Recommendation:</strong> ${item.suggestion}
      </div>
    </div>
  `).join('');
}
