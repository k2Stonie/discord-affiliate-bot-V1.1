/**
 * Discord Affiliate Bot Dashboard JavaScript
 * Handles all dashboard functionality, API calls, and real-time updates
 */

// Global variables
let socket = null;
let currentGuild = null;
let charts = {};
let dashboardData = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    setupWebSocket();
    loadInitialData();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    console.log('🚀 Initializing Discord Affiliate Bot Dashboard');
    
    // Setup navigation
    setupNavigation();
    
    // Initialize charts
    initializeCharts();
    
    // Setup tooltips
    initializeTooltips();
    
    // Setup modals
    initializeModals();
    
    console.log('✅ Dashboard initialized successfully');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('[onclick="refreshData()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }
    
    // Settings form
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsSubmit);
    }
    
    // Window events
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('resize', handleWindowResize);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * Setup navigation
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Get section name from onclick attribute
            const onclick = this.getAttribute('onclick');
            if (onclick) {
                const sectionName = onclick.match(/show(\w+)/);
                if (sectionName) {
                    showSection(sectionName[1].toLowerCase());
                }
            }
        });
    });
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Activity Chart
    const activityCtx = document.getElementById('activityChart');
    if (activityCtx) {
        charts.activity = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Messages Sent',
                    data: [12, 19, 3, 5, 2, 3, 8],
                    borderColor: '#5865F2',
                    backgroundColor: 'rgba(88, 101, 242, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Welcome Messages',
                    data: [8, 15, 2, 4, 1, 2, 6],
                    borderColor: '#3BA55C',
                    backgroundColor: 'rgba(59, 165, 92, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    // Messages Chart
    const messagesCtx = document.getElementById('messagesChart');
    if (messagesCtx) {
        charts.messages = new Chart(messagesCtx, {
            type: 'doughnut',
            data: {
                labels: ['Sent Successfully', 'Failed', 'Pending'],
                datasets: [{
                    data: [85, 10, 5],
                    backgroundColor: ['#3BA55C', '#ED4245', '#FAA61A'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
    
    // Campaigns Chart
    const campaignsCtx = document.getElementById('campaignsChart');
    if (campaignsCtx) {
        charts.campaigns = new Chart(campaignsCtx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Campaigns',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: 'rgba(88, 101, 242, 0.8)',
                    borderColor: '#5865F2',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Guild Modal
    const guildModal = document.getElementById('guildModal');
    if (guildModal) {
        guildModal.addEventListener('hidden.bs.modal', function() {
            currentGuild = null;
        });
    }
    
    // Campaign Modal
    const campaignModal = document.getElementById('campaignModal');
    if (campaignModal) {
        campaignModal.addEventListener('hidden.bs.modal', function() {
            // Reset campaign form
        });
    }
}

/**
 * Setup WebSocket connection
 */
function setupWebSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('🔌 Connected to dashboard WebSocket');
            updateBotStatus('online', 'Connected');
            showToast('Connected to dashboard', 'success');
        });
        
        socket.on('disconnect', function() {
            console.log('🔌 Disconnected from dashboard WebSocket');
            updateBotStatus('offline', 'Disconnected');
            showToast('Disconnected from dashboard', 'warning');
        });
        
        socket.on('bot_status_update', function(data) {
            console.log('🤖 Bot status update:', data);
            updateBotStatus(data.status, `${data.guild_count} servers`);
            updateDashboardStats(data);
        });
        
        socket.on('guild_joined', function(data) {
            console.log('➕ Guild joined:', data);
            showToast(`Bot joined server: ${data.name}`, 'success');
            loadGuilds();
        });
        
        socket.on('guild_left', function(data) {
            console.log('➖ Guild left:', data);
            showToast(`Bot left server: ${data.name}`, 'warning');
            loadGuilds();
        });
        
        socket.on('settings_updated', function(data) {
            console.log('⚙️ Settings updated:', data);
            showToast('Settings updated successfully', 'success');
            if (currentGuild && data.guild_id === currentGuild.id) {
                loadGuildDetails(currentGuild.id);
            }
        });
        
        socket.on('error', function(error) {
            console.error('❌ WebSocket error:', error);
            showToast('Connection error: ' + error.message, 'error');
        });
    } else {
        console.warn('⚠️ Socket.IO not loaded, real-time features disabled');
    }
}

/**
 * Load initial dashboard data
 */
async function loadInitialData() {
    try {
        showLoading(true);
        
        // Load overview data
        await loadOverviewData();
        
        // Load guilds
        await loadGuilds();
        
        console.log('✅ Initial data loaded successfully');
        
    } catch (error) {
        console.error('❌ Error loading initial data:', error);
        showToast('Error loading dashboard data', 'error');
    } finally {
        showLoading(false);
    }
}

/**
 * Load overview data
 */
async function loadOverviewData() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        dashboardData.analytics = data;
        updateOverviewStats(data);
        updateActivityChart(data);
        
    } catch (error) {
        console.error('Error loading overview data:', error);
        showToast('Error loading overview data', 'error');
    }
}

/**
 * Load guilds
 */
async function loadGuilds() {
    try {
        const response = await fetch('/api/guilds');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        dashboardData.guilds = data.guilds;
        renderGuilds(data.guilds);
        
    } catch (error) {
        console.error('Error loading guilds:', error);
        showToast('Error loading guilds', 'error');
    }
}

/**
 * Render guilds in the grid
 */
function renderGuilds(guilds) {
    const guildsGrid = document.getElementById('guildsGrid');
    const serverList = document.getElementById('serverList');

    [guildsGrid, serverList].forEach(container => {
        if (!container) return;
        container.innerHTML = '';
        guilds.forEach(guild => {
            const card = buildGuildCard(guild);
            container.appendChild(card);
        });
    });
}

function buildGuildCard(guild) {
    const cardWrapper = document.createElement('div');
    cardWrapper.className = 'col-md-6 col-lg-4 mb-4';

    const statusClass = guild.bot_connected ? 'bg-success' : 'bg-warning';
    const statusText = guild.bot_connected ? 'Connected' : 'Not Connected';
    const memberLabel = guild.member_label || `${guild.member_count} members`;
    const roleTag = guild.role_label ? `<small class="text-muted">${guild.role_label}</small>` : '';

    cardWrapper.innerHTML = `
        <div class="card guild-card h-100">
            <div class="card-body">
                <div class="d-flex align-items-center mb-3">
                    ${guild.icon ?
                        `<img src="${guild.icon}" class="guild-icon me-3" alt="${guild.name}">` :
                        `<div class="guild-icon-placeholder me-3"><i class="fas fa-server"></i></div>`
                    }
                    <div>
                        <h6 class="card-title mb-1">${escapeHtml(guild.name)}</h6>
                        ${roleTag}
                        <div><small class="text-muted">${memberLabel}</small></div>
                    </div>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="badge ${statusClass}">${statusText}</span>
                    <div class="action-container"></div>
                </div>
            </div>
        </div>
    `;

    const card = cardWrapper.querySelector('.guild-card');
    const actionContainer = cardWrapper.querySelector('.action-container');

    if (guild.bot_connected) {
        card.addEventListener('click', () => openGuildModal(guild.id));
        actionContainer.innerHTML = `
            <div class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-primary">Dashboard</button>
                <a class="btn btn-sm btn-primary" href="https://discord.com/channels/${guild.id}" target="_blank" rel="noopener">Open</a>
            </div>
        `;
        actionContainer.querySelector('button').addEventListener('click', event => {
            event.stopPropagation();
            openGuildModal(guild.id);
        });
    } else {
        card.addEventListener('click', () => connectGuild(guild.id));
        actionContainer.innerHTML = `
            <button class="btn btn-sm btn-primary">Connect</button>
        `;
        actionContainer.querySelector('button').addEventListener('click', event => {
            event.stopPropagation();
            connectGuild(guild.id);
        });
    }

    return cardWrapper;
}

function attachGuildCardHandlers(container) {
    container.querySelectorAll('.guild-card').forEach(card => {
        const guildId = card.dataset.guildId;
        const action = card.dataset.action;

        card.addEventListener('click', () => {
            if (action === 'open') {
                openGuildModal(guildId);
            } else if (action === 'connect') {
                connectGuild(guildId);
            }
        });

        card.querySelectorAll('[data-action="dashboard"]').forEach(btn => {
            btn.addEventListener('click', event => {
                event.stopPropagation();
                openGuildModal(guildId);
            });
        });

        card.querySelectorAll('[data-action="connect"]').forEach(btn => {
            btn.addEventListener('click', event => {
                event.stopPropagation();
                connectGuild(guildId);
            });
        });
    });
}

function connectGuild(guildId) {
    inviteBot(guildId);
}

function inviteBot(guildId) {
    window.open(`/invite/${guildId}`, '_blank');
}

/**
 * Open guild modal
 */
async function openGuildModal(guildId) {
    try {
        showLoading(true);
        
        const response = await fetch(`/api/guild/${guildId}`);
        const guildData = await response.json();
        
        if (guildData.error) {
            throw new Error(guildData.error);
        }
        
        currentGuild = guildData;
        renderGuildModal(guildData);
        
        const modal = new bootstrap.Modal(document.getElementById('guildModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error opening guild modal:', error);
        showToast('Error loading guild details', 'error');
    } finally {
        showLoading(false);
    }
}

/**
 * Render guild modal content
 */
function renderGuildModal(guildData) {
    const modalBody = document.getElementById('guildModalBody');
    
    const permissionsHTML = Object.entries(guildData.bot_permissions || {}).map(([perm, has]) => `
        <div class="permission-item">
            <i class="fas fa-${has ? 'check text-success' : 'times text-danger'} me-2"></i>
            <span>${perm.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
        </div>
    `).join('');
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="text-center">
                    ${guildData.icon ? 
                        `<img src="${guildData.icon}" class="img-fluid rounded mb-3" style="max-width: 150px;">` :
                        `<div class="bg-secondary rounded mb-3 d-flex align-items-center justify-content-center" style="width: 150px; height: 150px; margin: 0 auto;"><i class="fas fa-server fa-3x text-white"></i></div>`
                    }
                    <h5>${escapeHtml(guildData.name)}</h5>
                    <p class="text-muted">${guildData.member_count} members</p>
                </div>
            </div>
            <div class="col-md-8">
                <div class="row">
                    <div class="col-6">
                        <div class="stat-item">
                            <h6>Roles</h6>
                            <p class="text-primary">${guildData.roles?.length || 0}</p>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-item">
                            <h6>Channels</h6>
                            <p class="text-primary">${guildData.channels?.length || 0}</p>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h6>Bot Permissions</h6>
                    <div class="permissions-list">
                        ${permissionsHTML}
                    </div>
                </div>
                
                <div class="mt-4">
                    <button class="btn btn-primary" onclick="loadGuildSettings('${guildData.id}')">
                        <i class="fas fa-cog me-1"></i>Manage Settings
                    </button>
                    <button class="btn btn-outline-primary ms-2" onclick="loadGuildAnalytics('${guildData.id}')">
                        <i class="fas fa-chart-bar me-1"></i>View Analytics
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Update overview statistics
 */
function updateOverviewStats(data) {
    const elements = {
        totalServers: document.getElementById('totalServers'),
        totalMembers: document.getElementById('totalMembers'),
        activeCampaigns: document.getElementById('activeCampaigns'),
        messagesSent: document.getElementById('messagesSent')
    };
    
    if (elements.totalServers) {
        elements.totalServers.textContent = data.total_guilds || 0;
    }
    
    if (elements.totalMembers) {
        elements.totalMembers.textContent = data.total_members || 0;
    }
    
    if (elements.activeCampaigns) {
        elements.activeCampaigns.textContent = Object.keys(data.guild_analytics || {}).length;
    }
    
    if (elements.messagesSent) {
        let totalMessages = 0;
        Object.values(data.guild_analytics || {}).forEach(guild => {
            totalMessages += guild.message_sent_count || 0;
        });
        elements.messagesSent.textContent = totalMessages;
    }
}

/**
 * Update activity chart
 */
function updateActivityChart(data) {
    if (!charts.activity) return;
    
    // This would be populated with real data from the API
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const messageData = [12, 19, 3, 5, 2, 3, 8];
    const welcomeData = [8, 15, 2, 4, 1, 2, 6];
    
    charts.activity.data.labels = labels;
    charts.activity.data.datasets[0].data = messageData;
    charts.activity.data.datasets[1].data = welcomeData;
    charts.activity.update();
}

/**
 * Update bot status indicator
 */
function updateBotStatus(status, text) {
    const statusElement = document.getElementById('botStatus');
    if (!statusElement) return;
    
    const indicator = statusElement.querySelector('.status-indicator');
    const statusText = statusElement.querySelector('.status-text');
    
    if (indicator) {
        indicator.className = `status-indicator ${status}`;
    }
    
    if (statusText) {
        statusText.textContent = text;
    }
}

/**
 * Update dashboard stats from WebSocket data
 */
function updateDashboardStats(data) {
    if (data.guild_count !== undefined) {
        const totalServers = document.getElementById('totalServers');
        if (totalServers) {
            totalServers.textContent = data.guild_count;
        }
    }
}

/**
 * Show loading overlay
 */
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('d-none');
        } else {
            overlay.classList.add('d-none');
        }
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header i');
    
    if (toastBody) {
        toastBody.textContent = message;
    }
    
    if (toastHeader) {
        const iconMap = {
            'error': 'exclamation-triangle text-danger',
            'success': 'check-circle text-success',
            'warning': 'exclamation-circle text-warning',
            'info': 'info-circle text-primary'
        };
        
        toastHeader.className = `fas fa-${iconMap[type] || iconMap.info} me-2`;
    }
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

/**
 * Show section
 */
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Show selected section
    const sectionId = sectionName + 'Section';
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.remove('d-none');
    }
    
    // Update header
    updateContentHeader(sectionName);
    
    // Load section data
    loadSectionData(sectionName);
}

/**
 * Update content header
 */
function updateContentHeader(sectionName) {
    const titleElement = document.getElementById('contentTitle');
    const subtitleElement = document.getElementById('contentSubtitle');
    
    const headers = {
        'overview': {
            title: 'Dashboard Overview',
            subtitle: 'Welcome back! Here\'s what\'s happening with your bot.'
        },
        'guilds': {
            title: 'Server Management',
            subtitle: 'Manage your connected Discord servers.'
        },
        'campaigns': {
            title: 'Marketing Campaigns',
            subtitle: 'Create and manage your marketing campaigns.'
        },
        'targetroles': {
            title: 'Target Roles',
            subtitle: 'Configure roles for campaign targeting.'
        },
        'analytics': {
            title: 'Analytics Dashboard',
            subtitle: 'View detailed analytics and statistics.'
        },
        'settings': {
            title: 'Bot Settings',
            subtitle: 'Configure your bot settings and preferences.'
        }
    };
    
    const header = headers[sectionName] || headers.overview;
    
    if (titleElement) {
        titleElement.textContent = header.title;
    }
    
    if (subtitleElement) {
        subtitleElement.textContent = header.subtitle;
    }
}

/**
 * Load section data
 */
function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'guilds':
            loadGuilds();
            break;
        case 'campaigns':
            loadCampaigns();
            break;
        case 'targetroles':
            loadTargetRoles();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

/**
 * Handle refresh button click
 */
function handleRefresh() {
    const currentSection = document.querySelector('.content-section:not(.d-none)');
    if (currentSection) {
        const sectionId = currentSection.id;
        const sectionName = sectionId.replace('Section', '');
        loadSectionData(sectionName);
    }
    showToast('Data refreshed', 'success');
}

/**
 * Handle settings form submit
 */
function handleSettingsSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const settings = Object.fromEntries(formData.entries());
    
    // Add checkbox values
    settings.autoModeration = document.getElementById('autoModeration').checked;
    settings.welcomeMessages = document.getElementById('welcomeMessages').checked;
    
    saveSettings(settings);
}

/**
 * Save settings
 */
async function saveSettings(settings) {
    try {
        if (!currentGuild) {
            showToast('No guild selected', 'error');
            return;
        }
        
        const response = await fetch(`/api/guild/${currentGuild.id}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            throw new Error('Failed to save settings');
        }
        
    } catch (error) {
        console.error('Error saving settings:', error);
        showToast('Error saving settings', 'error');
    }
}

/**
 * Handle before unload
 */
function handleBeforeUnload(e) {
    if (socket && socket.connected) {
        socket.disconnect();
    }
}

/**
 * Handle window resize
 */
function handleWindowResize() {
    // Resize charts
    Object.values(charts).forEach(chart => {
        if (chart && chart.resize) {
            chart.resize();
        }
    });
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + R to refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        handleRefresh();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) {
                modal.hide();
            }
        }
    }
}

/**
 * Load guild settings
 */
async function loadGuildSettings(guildId) {
    try {
        const response = await fetch(`/api/guild/${guildId}/settings`);
        const settings = await response.json();
        
        // Populate settings form
        if (settings.prefix) {
            document.getElementById('botPrefix').value = settings.prefix;
        }
        if (settings.welcome_message) {
            document.getElementById('welcomeMessage').value = settings.welcome_message;
        }
        if (settings.auto_moderation !== undefined) {
            document.getElementById('autoModeration').checked = settings.auto_moderation;
        }
        if (settings.welcome_messages !== undefined) {
            document.getElementById('welcomeMessages').checked = settings.welcome_messages;
        }
        
        showToast('Settings loaded', 'success');
        
    } catch (error) {
        console.error('Error loading guild settings:', error);
        showToast('Error loading settings', 'error');
    }
}

/**
 * Load guild analytics
 */
async function loadGuildAnalytics(guildId) {
    try {
        const response = await fetch(`/api/analytics?guild_id=${guildId}`);
        const analytics = await response.json();
        
        if (analytics.error) {
            throw new Error(analytics.error);
        }
        
        // Display analytics in a modal or update charts
        showToast('Analytics loaded', 'success');
        
    } catch (error) {
        console.error('Error loading guild analytics:', error);
        showToast('Error loading analytics', 'error');
    }
}

/**
 * Load campaigns
 */
function loadCampaigns() {
    const campaignsList = document.getElementById('campaignsList');
    if (campaignsList) {
        campaignsList.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-bullhorn fa-3x mb-3"></i>
                <h5>No campaigns yet</h5>
                <p>Create your first marketing campaign to get started.</p>
                <button class="btn btn-primary" onclick="showCreateCampaign()">
                    <i class="fas fa-plus me-1"></i>Create Campaign
                </button>
            </div>
        `;
    }
}

/**
 * Load target roles
 */
function loadTargetRoles() {
    const targetRolesList = document.getElementById('targetRolesList');
    if (targetRolesList) {
        targetRolesList.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-users fa-3x mb-3"></i>
                <h5>No target roles configured</h5>
                <p>Add roles to target with your campaigns.</p>
                <button class="btn btn-primary" onclick="showAddTargetRole()">
                    <i class="fas fa-plus me-1"></i>Add Target Role
                </button>
            </div>
        `;
    }
}

/**
 * Load analytics
 */
function loadAnalytics() {
    showToast('Analytics loaded', 'success');
}

/**
 * Load settings
 */
function loadSettings() {
    if (!currentGuild) {
        showToast('Select a guild from Servers first', 'warning');
        return;
    }

    document.getElementById('contentTitle').textContent = 'Bot Settings';
    document.getElementById('contentSubtitle').textContent = `Configure settings for ${currentGuild.name}`;

    showLoading(true);

    fetch(`/api/guild/${currentGuild.id}/settings`)
        .then(res => res.json())
        .then(settings => {
            document.getElementById('botPrefix').value = settings.prefix || '!';
            document.getElementById('welcomeMessage').value = settings.welcome_message || '';
            document.getElementById('autoModeration').checked = !!settings.auto_moderation;
            document.getElementById('welcomeMessages').checked = !!settings.enable_welcome_messages;
            showToast('Settings loaded', 'success');
        })
        .catch(err => {
            console.error('Error loading settings:', err);
            showToast('Error loading settings', 'error');
        })
        .finally(() => showLoading(false));
}

/**
 * Show create campaign modal
 */
function showCreateCampaign() {
    showToast('Create campaign feature coming soon', 'info');
}

/**
 * Show add target role modal
 */
function showAddTargetRole() {
    showToast('Add target role feature coming soon', 'info');
}

/**
 * Show add server modal
 */
function showAddServer() {
    showToast('Add server feature coming soon', 'info');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format date
 */
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global access
window.showSection = showSection;
window.openGuildModal = openGuildModal;
window.loadGuildSettings = loadGuildSettings;
window.loadGuildAnalytics = loadGuildAnalytics;
window.showCreateCampaign = showCreateCampaign;
window.showAddTargetRole = showAddTargetRole;
window.showAddServer = showAddServer;
window.refreshData = handleRefresh;
window.connectGuild = connectGuild;
window.inviteBot = inviteBot;
