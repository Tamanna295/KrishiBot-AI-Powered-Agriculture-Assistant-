/**
 * KrishiBot — Agriculture WhatsApp AI Bot
 * Frontend JavaScript — connects UI to Flask backend
 */

const API_BASE = "/api";

// --- DOM References ---
const stateSelect = document.getElementById("stateSelect");
const districtSelect = document.getElementById("districtSelect");
const langSelect = document.getElementById("langSelect");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const chatStatus = document.getElementById("chatStatus");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const sidebar = document.getElementById("sidebar");

// Category buttons
const categoryBtns = document.querySelectorAll(".category-btn");

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------
function getTime() {
    return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// ---------------------------------------------------------------------------
// Message rendering
// ---------------------------------------------------------------------------
function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user-message fade-in";
    div.innerHTML = `
        <div class="message-content"><p>${text}</p></div>
        <span class="message-time">${getTime()} ✓✓</span>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function addBotMessage(html) {
    // Remove typing indicator first
    removeTyping();
    const div = document.createElement("div");
    div.className = "message bot-message fade-in";
    div.innerHTML = `
        <div class="message-content">${html}</div>
        <span class="message-time">${getTime()}</span>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const existing = chatMessages.querySelector(".typing-message");
    if (existing) return;
    const div = document.createElement("div");
    div.className = "message bot-message typing-message";
    div.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const t = chatMessages.querySelector(".typing-message");
    if (t) t.remove();
}

function addErrorMessage(msg) {
    removeTyping();
    addBotMessage(`<p>❌ <strong>Error:</strong> ${msg}</p>
        <p><em>Make sure the Flask backend is running on port 5000.</em></p>`);
}

// ---------------------------------------------------------------------------
// API fetch helper
// ---------------------------------------------------------------------------
async function apiFetch(endpoint, params = {}) {
    const url = new URL(`${window.location.origin}${API_BASE}/${endpoint}`);
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
    // Cache-busting to prevent stale language data
    url.searchParams.set("_t", Date.now());
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// ---------------------------------------------------------------------------
// Populate states
// ---------------------------------------------------------------------------
async function loadStates() {
    try {
        const data = await apiFetch("states");
        data.states.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s;
            opt.textContent = s;
            stateSelect.appendChild(opt);
        });
    } catch {
        // Fallback: hardcode common states
        const states = [
            "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
            "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
            "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
            "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ];
        states.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s; opt.textContent = s;
            stateSelect.appendChild(opt);
        });
    }
}

// ---------------------------------------------------------------------------
// Populate districts when state changes
// ---------------------------------------------------------------------------
stateSelect.addEventListener("change", async () => {
    const state = stateSelect.value;
    districtSelect.innerHTML = '<option value="">Select District...</option>';
    districtSelect.disabled = !state;

    if (!state) {
        chatStatus.textContent = "Select your state & district to get started";
        return;
    }
    chatStatus.textContent = `📍 ${state} — loading districts...`;

    try {
        const data = await apiFetch("districts", { state });
        data.districts.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d; opt.textContent = d;
            districtSelect.appendChild(opt);
        });
        chatStatus.textContent = `📍 ${state} — select a district`;
    } catch {
        chatStatus.textContent = `📍 ${state} — select a district manually`;
    }
});

districtSelect.addEventListener("change", () => {
    const state = stateSelect.value;
    const district = districtSelect.value;
    if (state && district) {
        chatStatus.textContent = `📍 ${state} → ${district} — Ready!`;
    }
});

// Language change listener — show feedback and auto-refresh
langSelect.addEventListener("change", () => {
    const langName = langSelect.options[langSelect.selectedIndex].textContent;
    addBotMessage(`<p>🌐 Language changed to <strong>${langName}</strong>. Crop names will now appear in the selected language.</p>`);
    // Auto-refresh crop advice if state is selected
    const state = stateSelect.value;
    if (state) {
        const district = districtSelect.value;
        const lang = langSelect.value;
        handleAdvice(state, district, lang);
    }
});

// ---------------------------------------------------------------------------
// Category handlers
// ---------------------------------------------------------------------------
categoryBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        const cat = btn.dataset.category;
        handleCategory(cat);
        // Close mobile sidebar
        sidebar.classList.remove("open");
    });
});

async function handleCategory(category) {
    const state = stateSelect.value;
    const district = districtSelect.value;
    const lang = langSelect.value;

    if (!state && category !== "market") {
        addBotMessage("<p>⚠️ Please select a <strong>State</strong> from the sidebar first.</p>");
        return;
    }

    switch (category) {
        case "advice": return handleAdvice(state, district, lang);
        case "soil": return handleSoilHealth(state, lang);
        case "weather": return handleWeather(state, district);
        case "market": return handleMarketPrices();
        case "pesticide": return handlePesticides(state);
        case "yield": return handleCropYield(state);
    }
}

// ---------------------------------------------------------------------------
// 1. Crop Advice
// ---------------------------------------------------------------------------
async function handleAdvice(state, district, lang) {
    addUserMessage(`🌱 Get crop recommendations for ${state}${district ? ' → ' + district : ''}`);
    showTyping();

    try {
        const data = await apiFetch("advice", { state, district, lang });

        let html = `<p>🌱 <strong>Crop Recommendations</strong> for <strong>${state}</strong>`;
        if (district) html += ` → <strong>${district}</strong>`;
        html += `</p>`;

        // Soil info
        if (data.soil && !data.soil.error) {
            html += `
                <div class="data-card">
                    <div class="data-card-title">🧪 Local Soil Profile</div>
                    <div class="data-row"><span class="data-label">Nitrogen (N)</span><span class="data-value">${data.soil.N} kg/ha</span></div>
                    <div class="data-row"><span class="data-label">Phosphorus (P)</span><span class="data-value">${data.soil.P} kg/ha</span></div>
                    <div class="data-row"><span class="data-label">Potassium (K)</span><span class="data-value">${data.soil.K} kg/ha</span></div>
                    <div class="data-row"><span class="data-label">pH</span><span class="data-value">${data.soil.pH}</span></div>
                </div>`;
        }

        // Weather snippet
        if (data.weather && data.weather.temperature !== null) {
            html += `
                <div class="data-card">
                    <div class="data-card-title">🌤️ Current Weather</div>
                    <div class="data-row"><span class="data-label">Temperature</span><span class="data-value">${data.weather.temperature}°C</span></div>
                    <div class="data-row"><span class="data-label">Humidity</span><span class="data-value">${data.weather.humidity || '—'}%</span></div>
                    <div class="data-row"><span class="data-label">Condition</span><span class="data-value">${data.weather.condition || '—'}</span></div>
                </div>`;
        }

        // Rainfall
        if (data.rainfall && data.rainfall.annual) {
            html += `
                <div class="data-card">
                    <div class="data-card-title">🌧️ Rainfall Normal</div>
                    <div class="data-row"><span class="data-label">Annual</span><span class="data-value">${data.rainfall.annual} mm</span></div>
                </div>`;
        }

        // Top crops
        if (data.top_crops && data.top_crops.length > 0) {
            html += `<p style="margin-top:10px">🏆 <strong>Top ${data.top_crops.length} Recommended Crops:</strong></p>`;
            data.top_crops.forEach((crop, i) => {
                const ic = crop.ideal_conditions;
                html += `
                    <div class="crop-card">
                        <span class="crop-rank">${i + 1}</span>
                        <span class="crop-name">${crop.crop}</span>
                        <span class="crop-score">${crop.match_score}% match</span>
                        <div class="crop-conditions">
                            <div class="condition-chip"><span class="label">N</span>${ic.N}</div>
                            <div class="condition-chip"><span class="label">P</span>${ic.P}</div>
                            <div class="condition-chip"><span class="label">K</span>${ic.K}</div>
                            <div class="condition-chip"><span class="label">pH</span>${ic.pH}</div>
                            <div class="condition-chip"><span class="label">Temp</span>${ic.temperature}°C</div>
                            <div class="condition-chip"><span class="label">Rain</span>${ic.rainfall}mm</div>
                        </div>
                    </div>`;
            });
        } else {
            html += `<p>⚠️ Could not compute crop recommendations. Check soil/weather data availability.</p>`;
        }

        // Pesticide note
        if (data.pesticide_advice && data.pesticide_advice.recommendation) {
            html += `<p style="margin-top:8px;font-size:.88rem">${data.pesticide_advice.recommendation}</p>`;
        }

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// 2. Soil Health
// ---------------------------------------------------------------------------
async function handleSoilHealth(state, lang) {
    addUserMessage(`🧪 Show soil health for ${state}`);
    showTyping();

    try {
        const data = await apiFetch("soil-health", { state, lang });

        let html = `<p>🧪 <strong>Soil Health Report — ${state}</strong></p>`;

        html += `
            <div class="data-card">
                <div class="data-card-title">📊 NPK & pH Values</div>
                <div class="data-row"><span class="data-label">Nitrogen (N)</span><span class="data-value">${data.nitrogen_N} kg/ha</span></div>
                <div class="data-row"><span class="data-label">Phosphorus (P)</span><span class="data-value">${data.phosphorus_P} kg/ha</span></div>
                <div class="data-row"><span class="data-label">Potassium (K)</span><span class="data-value">${data.potassium_K} kg/ha</span></div>
                <div class="data-row"><span class="data-label">pH Level</span><span class="data-value">${data.pH}</span></div>
            </div>`;

        // Tips
        if (data.soil_health_tips && data.soil_health_tips.length > 0) {
            html += `<div class="data-card"><div class="data-card-title">💡 Recommendations</div>`;
            data.soil_health_tips.forEach(tip => {
                html += `<div class="tip-item">${tip}</div>`;
            });
            html += `</div>`;
        }

        // Suitable crops
        if (data.suitable_crops && data.suitable_crops.length > 0) {
            html += `<p style="margin-top:8px">🌾 <strong>Suitable Crops:</strong> ${data.suitable_crops.join(", ")}</p>`;
        }

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// 3. Weather
// ---------------------------------------------------------------------------
async function handleWeather(state, district) {
    addUserMessage(`🌦️ Weather for ${state}${district ? ' → ' + district : ''}`);
    showTyping();

    try {
        const data = await apiFetch("weather", { state, district });
        let html = `<p>🌦️ <strong>Weather Report</strong> — ${state}`;
        if (district) html += ` → ${district}`;
        html += `</p>`;

        if (data.weather) {
            const w = data.weather;
            html += `
                <div class="data-card">
                    <div class="data-card-title">🌤️ Current Conditions</div>
                    <div class="data-row"><span class="data-label">Temperature</span><span class="data-value" style="font-size:1.1rem">${w.temperature !== null ? w.temperature + '°C' : '—'}</span></div>
                    <div class="data-row"><span class="data-label">Condition</span><span class="data-value">${w.condition || '—'}</span></div>
                    <div class="data-row"><span class="data-label">Humidity</span><span class="data-value">${w.humidity !== null ? w.humidity + '%' : '—'}</span></div>
                    <div class="data-row"><span class="data-label">Wind Speed</span><span class="data-value">${w.wind_speed !== null ? w.wind_speed + ' km/h' : '—'}</span></div>
                    ${w.last_updated ? `<div class="data-row"><span class="data-label">Updated</span><span class="data-value" style="font-size:.78rem">${w.last_updated}</span></div>` : ''}
                </div>`;
        } else {
            html += `<p>⚠️ No weather data available for this location.</p>`;
        }

        // Rainfall
        if (data.rainfall_normal) {
            const rn = data.rainfall_normal;
            html += `
                <div class="data-card">
                    <div class="data-card-title">🌧️ Rainfall Normal</div>
                    <div class="data-row"><span class="data-label">Annual Total</span><span class="data-value" style="font-size:1.05rem">${rn.annual ? rn.annual + ' mm' : '—'}</span></div>
                </div>`;

            // Monthly chart as mini bars
            if (rn.monthly) {
                const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
                const vals = months.map(m => rn.monthly[m] || 0);
                const maxVal = Math.max(...vals, 1);
                html += `<div class="data-card"><div class="data-card-title">📅 Monthly Rainfall (mm)</div>`;
                html += `<div style="display:flex;align-items:flex-end;gap:4px;height:80px;margin-top:8px">`;
                months.forEach((m, i) => {
                    const h = Math.max(2, (vals[i] / maxVal) * 70);
                    const color = vals[i] > 200 ? 'var(--wa-accent)' : vals[i] > 50 ? 'var(--wa-green)' : 'var(--wa-text-muted)';
                    html += `<div style="flex:1;display:flex;flex-direction:column;align-items:center">
                        <div style="font-size:.55rem;color:var(--wa-text-muted);margin-bottom:2px">${vals[i].toFixed(0)}</div>
                        <div style="width:100%;height:${h}px;background:${color};border-radius:3px 3px 0 0;transition:height .3s"></div>
                        <div style="font-size:.55rem;color:var(--wa-text-muted);margin-top:3px">${m.slice(0, 1)}</div>
                    </div>`;
                });
                html += `</div></div>`;
            }
        }

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// 4. Market Prices
// ---------------------------------------------------------------------------
async function handleMarketPrices() {
    addUserMessage("📊 Show latest market prices");
    showTyping();

    try {
        const data = await apiFetch("market-prices");
        let html = `<p>📊 <strong>Commodity Market Prices</strong></p>
            <p style="font-size:.8rem;color:var(--wa-text-muted)">Report Date: ${data.report_date || '—'}</p>`;

        if (data.prices && data.prices.length > 0) {
            html += `<div style="overflow-x:auto">
                <table class="price-table">
                    <thead><tr>
                        <th>Commodity</th>
                        <th>MSP</th>
                        <th>Latest ₹</th>
                        <th>Prev ₹</th>
                        <th>Arrivals</th>
                    </tr></thead><tbody>`;

            data.prices.forEach(p => {
                html += `<tr>
                    <td><strong>${p.commodity}</strong><br><span style="font-size:.7rem;color:var(--wa-text-muted)">${p.commodity_group}</span></td>
                    <td>${p.msp}</td>
                    <td>${p.price_latest}</td>
                    <td>${p.price_prev1}</td>
                    <td>${p.arrival_latest}</td>
                </tr>`;
            });
            html += `</tbody></table></div>`;
        } else {
            html += `<p>No market price data available.</p>`;
        }

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// 5. Pesticides
// ---------------------------------------------------------------------------
async function handlePesticides(state) {
    addUserMessage(`🛡️ Pesticide guide for ${state}`);
    showTyping();

    try {
        const data = await apiFetch("pesticides", { state });
        let html = `<p>🛡️ <strong>Pesticide Guide — ${state}</strong></p>`;

        // --- Bio-Pesticide Names Table ---
        if (data.bio_pesticides && data.bio_pesticides.length > 0) {
            html += `<div class="data-card"><div class="data-card-title">🌿 Recommended Bio-Pesticides</div>`;
            html += `<div style="overflow-x:auto">
                <table class="price-table">
                    <thead><tr>
                        <th>Pesticide Name</th>
                        <th>Type</th>
                        <th>Target Pest/Disease</th>
                        <th>Applicable Crops</th>
                    </tr></thead><tbody>`;
            data.bio_pesticides.forEach(p => {
                html += `<tr>
                    <td><strong>${p.name}</strong></td>
                    <td><span style="background:rgba(0,168,132,.15);padding:2px 8px;border-radius:10px;font-size:.78rem">${p.type}</span></td>
                    <td>${p.target}</td>
                    <td style="font-size:.82rem;color:var(--wa-text-muted)">${p.crops}</td>
                </tr>`;
            });
            html += `</tbody></table></div></div>`;
        }

        // --- Bio-Pesticide Demand Data ---
        if (data.bio_demand && data.bio_demand.yearly_demand_mt) {
            html += `<div class="data-card"><div class="data-card-title">📊 Bio-Pesticide Demand — ${state} (${data.bio_demand.unit})</div>`;
            Object.entries(data.bio_demand.yearly_demand_mt).forEach(([year, val]) => {
                html += `<div class="data-row"><span class="data-label">${year}</span><span class="data-value">${Number(val).toLocaleString()} MT</span></div>`;
            });
            html += `</div>`;
        }

        // --- Chemical Pesticide Names Table ---
        if (data.chemical_pesticides && data.chemical_pesticides.length > 0) {
            html += `<div class="data-card"><div class="data-card-title">⚗️ Chemical Pesticides Reference</div>`;
            html += `<div style="overflow-x:auto">
                <table class="price-table">
                    <thead><tr>
                        <th>Pesticide Name</th>
                        <th>Type</th>
                        <th>Target Pest/Disease</th>
                        <th>Applicable Crops</th>
                    </tr></thead><tbody>`;
            data.chemical_pesticides.forEach(p => {
                html += `<tr>
                    <td><strong>${p.name}</strong></td>
                    <td><span style="background:rgba(255,87,87,.15);padding:2px 8px;border-radius:10px;font-size:.78rem">${p.type}</span></td>
                    <td>${p.target}</td>
                    <td style="font-size:.82rem;color:var(--wa-text-muted)">${p.crops}</td>
                </tr>`;
            });
            html += `</tbody></table></div></div>`;
        }

        // --- Chemical Pesticide Demand Data ---
        if (data.chemical_demand && data.chemical_demand.yearly_demand_mt) {
            html += `<div class="data-card"><div class="data-card-title">📊 Chemical Pesticide Demand — ${state} (${data.chemical_demand.unit})</div>`;
            Object.entries(data.chemical_demand.yearly_demand_mt).forEach(([year, val]) => {
                html += `<div class="data-row"><span class="data-label">${year}</span><span class="data-value">${Number(val).toLocaleString()} MT</span></div>`;
            });
            html += `</div>`;
        }

        if (!data.bio_pesticides && !data.chemical_pesticides) {
            html += `<p>⚠️ No pesticide data found for ${state}.</p>`;
        }

        html += `<p style="margin-top:8px;padding:10px;background:rgba(0,168,132,.1);border-radius:8px;font-size:.9rem">${data.recommendation}</p>`;

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// 6. Crop Yield
// ---------------------------------------------------------------------------
async function handleCropYield(state) {
    addUserMessage(`📈 Crop yield data for ${state}`);
    showTyping();

    try {
        const data = await apiFetch("crop-yield", { state });
        let html = `<p>📈 <strong>Crop Yield Data — ${state}</strong></p>`;

        if (data.crop_yield && data.crop_yield.length > 0) {
            html += `<div style="overflow-x:auto">
                <table class="price-table">
                    <thead><tr>
                        <th>Crop</th>
                        <th>Year</th>
                        <th>Season</th>
                        <th>Production</th>
                        <th>Yield</th>
                    </tr></thead><tbody>`;

            data.crop_yield.forEach(c => {
                html += `<tr>
                    <td><strong>${c.crop}</strong></td>
                    <td>${c.year || '—'}</td>
                    <td>${c.season}</td>
                    <td>${c.production !== null ? c.production.toLocaleString() : '—'}</td>
                    <td>${c.yield !== null ? c.yield.toFixed(2) : '—'}</td>
                </tr>`;
            });
            html += `</tbody></table></div>`;
        } else {
            html += `<p>No crop yield data available for ${state}.</p>`;
        }

        addBotMessage(html);
    } catch (e) {
        addErrorMessage(e.message);
    }
}

// ---------------------------------------------------------------------------
// Text input handler (free-form chat)
// ---------------------------------------------------------------------------
function handleTextInput() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = "";
    addUserMessage(text);
    showTyping();

    const lower = text.toLowerCase();
    const state = stateSelect.value;
    const district = districtSelect.value;
    const lang = langSelect.value;

    // Simple keyword matching
    setTimeout(() => {
        if (lower.includes("crop") || lower.includes("recommend") || lower.includes("suggest") || lower.includes("advice")) {
            if (state) { handleAdvice(state, district, lang); }
            else { addBotMessage("<p>Please select a <strong>State</strong> first, then ask for crop advice! 👈</p>"); }
        }
        else if (lower.includes("soil") || lower.includes("npk") || lower.includes("ph")) {
            if (state) { handleSoilHealth(state, lang); }
            else { addBotMessage("<p>Please select a <strong>State</strong> to check soil health! 👈</p>"); }
        }
        else if (lower.includes("weather") || lower.includes("rain") || lower.includes("temperature") || lower.includes("climate")) {
            if (state) { handleWeather(state, district); }
            else { addBotMessage("<p>Please select a <strong>State</strong> & <strong>District</strong> for weather data! 👈</p>"); }
        }
        else if (lower.includes("price") || lower.includes("market") || lower.includes("msp") || lower.includes("rate")) {
            handleMarketPrices();
        }
        else if (lower.includes("pesticide") || lower.includes("pest") || lower.includes("insect") || lower.includes("spray")) {
            if (state) { handlePesticides(state); }
            else { addBotMessage("<p>Please select a <strong>State</strong> for pesticide info! 👈</p>"); }
        }
        else if (lower.includes("yield") || lower.includes("production") || lower.includes("harvest")) {
            if (state) { handleCropYield(state); }
            else { addBotMessage("<p>Please select a <strong>State</strong> for yield data! 👈</p>"); }
        }
        else if (lower.includes("hello") || lower.includes("hi") || lower.includes("namaste")) {
            addBotMessage("<p>🙏 Namaste! How can I help you today?</p><p>Try asking about <strong>crop recommendations</strong>, <strong>soil health</strong>, <strong>weather</strong>, <strong>market prices</strong>, or <strong>pesticides</strong>.</p>");
        }
        else if (lower.includes("help")) {
            addBotMessage(`
                <p>🆘 <strong>Here's what I can do:</strong></p>
                <ul>
                    <li><strong>Crop advice</strong> — "Suggest crops for my area"</li>
                    <li><strong>Soil health</strong> — "Show soil NPK data"</li>
                    <li><strong>Weather</strong> — "What's the weather?"</li>
                    <li><strong>Market prices</strong> — "Show market rates"</li>
                    <li><strong>Pesticides</strong> — "Pesticide recommendations"</li>
                    <li><strong>Crop yield</strong> — "Show production data"</li>
                </ul>
                <p>Or simply click the category buttons on the left! 👈</p>
            `);
        }
        else {
            addBotMessage(`
                <p>🤔 I'm not sure about that. Try one of these:</p>
                <ul>
                    <li>🌱 "Suggest crops"</li>
                    <li>🧪 "Soil health"</li>
                    <li>🌦️ "Weather update"</li>
                    <li>📊 "Market prices"</li>
                    <li>🛡️ "Pesticide guide"</li>
                    <li>📈 "Crop yield"</li>
                </ul>
            `);
        }
    }, 600);
}

sendBtn.addEventListener("click", handleTextInput);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleTextInput();
});

// ---------------------------------------------------------------------------
// Mobile menu toggle
// ---------------------------------------------------------------------------
mobileMenuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
});

// Close sidebar when clicking outside on mobile
document.addEventListener("click", (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains("open")) {
        if (!sidebar.contains(e.target) && e.target !== mobileMenuBtn) {
            sidebar.classList.remove("open");
        }
    }
});

// ---------------------------------------------------------------------------
// Initialize
// ---------------------------------------------------------------------------
loadStates();

// ---------------------------------------------------------------------------
// Session ID (farmer profile)
// ---------------------------------------------------------------------------
function getSessionId() {
    let sid = localStorage.getItem("krishi_session");
    if (!sid) {
        sid = "sess_" + Math.random().toString(36).substr(2, 12) + Date.now();
        localStorage.setItem("krishi_session", sid);
    }
    return sid;
}

async function loadProfile() {
    const sid = getSessionId();
    try {
        const data = await apiFetch("profile", { session_id: sid });
        if (data.profile) {
            const p = data.profile;
            if (p.state)    stateSelect.value = p.state;
            if (p.language) langSelect.value  = p.language;
            if (p.state) {
                stateSelect.dispatchEvent(new Event("change"));
                setTimeout(() => {
                    if (p.district) {
                        districtSelect.value = p.district;
                        districtSelect.dispatchEvent(new Event("change"));
                    }
                }, 800);
            }
        }
        if (data.history && data.history.length > 0) {
            showHistory(data.history);
        }
    } catch (e) { /* profile load is optional */ }
}

function showHistory(history) {
    const panel = document.getElementById("historyPanel");
    const list  = document.getElementById("historyList");
    if (!panel || !list) return;
    panel.style.display = "block";
    const icons = { advice:"🌱", soil:"🧪", weather:"🌦️", market:"📊", pesticide:"🛡️", yield:"📈" };
    list.innerHTML = history.slice(0, 5).map(h => `
        <div class="history-item" onclick="handleCategory('${h.category}')">
            <span>${icons[h.category] || "📌"}</span>
            <span class="h-cat">${h.category}</span>
            <span style="margin-left:auto;font-size:.65rem">${h.state || ""}</span>
        </div>`).join("");
}

async function saveProfile() {
    try {
        await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: getSessionId(),
                state:      stateSelect.value,
                district:   districtSelect.value,
                language:   langSelect.value,
            })
        });
    } catch (e) { /* non-critical */ }
}

async function logHistory(category, topCrop = "") {
    try {
        await fetch("/api/history", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: getSessionId(),
                category,
                state:    stateSelect.value,
                district: districtSelect.value,
                top_crop: topCrop,
            })
        });
    } catch (e) { /* non-critical */ }
}

// Save profile whenever location changes
stateSelect.addEventListener("change",    saveProfile);
districtSelect.addEventListener("change", saveProfile);
langSelect.addEventListener("change",     saveProfile);

// Load profile on start (after states load)
setTimeout(loadProfile, 600);

// ---------------------------------------------------------------------------
// Chart.js helpers
// ---------------------------------------------------------------------------
const _charts = {};

function destroyChart(id) {
    if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}

function buildCropScoreChart(containerId, crops) {
    destroyChart(containerId);
    const canvas = document.getElementById(containerId);
    if (!canvas || typeof Chart === "undefined") return;
    _charts[containerId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels: crops.map(c => c.crop.split(" (")[0].substring(0, 14)),
            datasets: [{
                label: "Match Score (%)",
                data:  crops.map(c => c.match_score),
                backgroundColor: crops.map((_, i) =>
                    i === 0 ? "rgba(0,168,132,0.85)" :
                    i === 1 ? "rgba(0,168,132,0.6)"  :
                              "rgba(0,168,132,0.35)"),
                borderColor:     "rgba(0,168,132,1)",
                borderWidth: 1,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, ticks: { color: "#8696A0", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.05)" } },
                x: { ticks: { color: "#8696A0", font: { size: 10 } }, grid: { display: false } }
            }
        }
    });
}

function buildRainfallChart(containerId, monthly) {
    destroyChart(containerId);
    const canvas = document.getElementById(containerId);
    if (!canvas || typeof Chart === "undefined") return;
    const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
    const vals   = months.map(m => monthly[m] || 0);
    _charts[containerId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels: months.map(m => m[0]),
            datasets: [{
                data: vals,
                backgroundColor: vals.map(v => v > 200 ? "rgba(83,189,235,0.85)" : v > 50 ? "rgba(0,168,132,0.7)" : "rgba(134,150,160,0.4)"),
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + " mm" } } },
            scales: {
                y: { ticks: { color: "#8696A0", font: { size: 9 } }, grid: { color: "rgba(255,255,255,0.05)" } },
                x: { ticks: { color: "#8696A0", font: { size: 9 } }, grid: { display: false } }
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Override handleAdvice to use Chart.js and log history
// ---------------------------------------------------------------------------
const _origHandleAdvice = handleAdvice;
handleAdvice = async function(state, district, lang) {
    addUserMessage(`🌱 Get crop recommendations for ${state}${district ? " → " + district : ""}`);
    showTyping();
    try {
        const data = await apiFetch("advice", { state, district, lang });
        let html = `<p>🌱 <strong>Crop Recommendations</strong> for <strong>${state}</strong>`;
        if (district) html += ` → <strong>${district}</strong>`;
        if (data.ml_used) html += ` <span class="method-badge">🤖 RandomForest ML</span>`;
        html += "</p>";

        if (data.soil && !data.soil.error) {
            const s = data.soil;
            html += `<div class="data-card"><div class="data-card-title">🧪 Soil Profile</div>
                <div class="data-row"><span class="data-label">N</span><span class="data-value">${s.N} kg/ha</span></div>
                <div class="data-row"><span class="data-label">P</span><span class="data-value">${s.P} kg/ha</span></div>
                <div class="data-row"><span class="data-label">K</span><span class="data-value">${s.K} kg/ha</span></div>
                <div class="data-row"><span class="data-label">pH</span><span class="data-value">${s.pH}</span></div></div>`;
        }
        if (data.weather && data.weather.temperature !== null) {
            const w = data.weather;
            const src = w.source === "live_openweathermap" ? " 🔴 Live" : " (CSV)";
            html += `<div class="data-card"><div class="data-card-title">🌤️ Weather${src}</div>
                <div class="data-row"><span class="data-label">Temperature</span><span class="data-value">${w.temperature}°C</span></div>
                <div class="data-row"><span class="data-label">Humidity</span><span class="data-value">${w.humidity||"—"}%</span></div>
                <div class="data-row"><span class="data-label">Condition</span><span class="data-value">${w.condition||"—"}</span></div></div>`;
        }

        const chartId = "cropChart_" + Date.now();
        if (data.top_crops && data.top_crops.length > 0) {
            html += `<p style="margin-top:10px">🏆 <strong>Top ${data.top_crops.length} Recommended Crops:</strong></p>`;
            html += `<div class="chart-container"><div class="chart-title">Match Score Comparison</div><canvas id="${chartId}" height="130"></canvas></div>`;
            data.top_crops.forEach((crop, i) => {
                const ic = crop.ideal_conditions || {};
                html += `<div class="crop-card">
                    <span class="crop-rank">${i+1}</span>
                    <span class="crop-name">${crop.crop}</span>
                    <span class="crop-score">${crop.match_score}%</span>
                    <div class="score-bar-wrap"><div class="score-bar-bg"><div class="score-bar-fill" style="width:${crop.match_score}%"></div></div><span class="score-pct">${crop.match_score}%</span></div>
                    ${ic.N !== undefined ? `<div class="crop-conditions">
                        <div class="condition-chip"><span class="label">N</span>${ic.N}</div>
                        <div class="condition-chip"><span class="label">P</span>${ic.P}</div>
                        <div class="condition-chip"><span class="label">K</span>${ic.K}</div>
                        <div class="condition-chip"><span class="label">pH</span>${ic.pH}</div>
                        <div class="condition-chip"><span class="label">Temp</span>${ic.temperature}°C</div>
                        <div class="condition-chip"><span class="label">Rain</span>${ic.rainfall}mm</div>
                    </div>` : ""}
                </div>`;
            });
        }
        addBotMessage(html);
        setTimeout(() => buildCropScoreChart(chartId, data.top_crops || []), 100);
        logHistory("advice", (data.top_crops[0] || {}).crop || "");
    } catch(e) { addErrorMessage(e.message); }
};

// ---------------------------------------------------------------------------
// Override handleWeather to use Chart.js rainfall chart
// ---------------------------------------------------------------------------
const _origHandleWeather = handleWeather;
handleWeather = async function(state, district) {
    addUserMessage(`🌦️ Weather for ${state}${district ? " → " + district : ""}`);
    showTyping();
    try {
        const data = await apiFetch("weather", { state, district });
        let html = `<p>🌦️ <strong>Weather Report</strong> — ${state}${district ? " → " + district : ""}</p>`;
        if (data.weather) {
            const w   = data.weather;
            const src = w.source === "live_openweathermap" ? " 🔴 Live" : " (CSV)";
            html += `<div class="data-card"><div class="data-card-title">🌤️ Conditions${src}</div>
                <div class="data-row"><span class="data-label">Temperature</span><span class="data-value" style="font-size:1.1rem">${w.temperature !== null ? w.temperature + "°C" : "—"}</span></div>
                <div class="data-row"><span class="data-label">Condition</span><span class="data-value">${w.condition||"—"}</span></div>
                <div class="data-row"><span class="data-label">Humidity</span><span class="data-value">${w.humidity !== null ? w.humidity + "%" : "—"}</span></div>
                <div class="data-row"><span class="data-label">Wind Speed</span><span class="data-value">${w.wind_speed !== null ? w.wind_speed + " km/h" : "—"}</span></div></div>`;
        } else {
            html += `<p>⚠️ No weather data available for this location.</p>`;
        }
        const rainChartId = "rainChart_" + Date.now();
        if (data.rainfall_normal) {
            const rn = data.rainfall_normal;
            html += `<div class="data-card"><div class="data-card-title">🌧️ Annual Rainfall</div>
                <div class="data-row"><span class="data-label">Annual Total</span><span class="data-value">${rn.annual ? rn.annual + " mm" : "—"}</span></div></div>`;
            if (rn.monthly) {
                html += `<div class="chart-container"><div class="chart-title">📅 Monthly Rainfall (mm)</div><canvas id="${rainChartId}" height="120"></canvas></div>`;
            }
        }
        addBotMessage(html);
        if (data.rainfall_normal && data.rainfall_normal.monthly) {
            setTimeout(() => buildRainfallChart(rainChartId, data.rainfall_normal.monthly), 100);
        }
        logHistory("weather");
    } catch(e) { addErrorMessage(e.message); }
};
