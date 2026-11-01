/**
 * Portfolio Agent — Studio Web Application
 * Modern Light Design System with SVG vector icons and zero emojis.
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================
    // Application State
    // =========================================================
    const state = {
        mode: 'prompt', // 'prompt' | 'wizard'
        activeTab: 'agent', // 'agent' | 'preview' | 'code' | 'export'
        device: 'desktop', // 'desktop' | 'laptop' | 'tablet' | 'mobile'
        isLandscape: false,
        isGenerating: false,
        autoscroll: true,
        currentJobId: null,
        currentSiteId: null,
        activeCodeFile: 'index.html',
        config: null,
        eventSource: null,
        wizardSkills: ['Python', 'TypeScript', 'React', 'FastAPI', 'PyTorch', 'Docker', 'Tailwind CSS'],
        wizardProjects: [
            {
                name: 'Autonomous Agent Framework',
                tag: 'AI / SYSTEMS',
                tech: 'Python, OpenAI, FastAPI',
                desc: 'Sandboxed multi-agent orchestration engine for production website generation.'
            },
            {
                name: 'Reactive Telemetry Dashboard',
                tag: 'FULL-STACK',
                tech: 'TypeScript, React, WebSockets',
                desc: 'Real-time distributed metrics ingestion pipeline and interactive visualizer.'
            }
        ],
        presets: {
            'ai-engineer': {
                prompt: 'Build a modern, clean light-themed portfolio for Dr. Elena Vance, Senior AI Systems Architect and Machine Learning Researcher. Include a high-impact minimalist hero section with crisp typography, an interactive technical competencies grid (PyTorch, CUDA, Distributed Training, LLM fine-tuning), research publication list with DOI links, featured open-source project cards with repository and live demo links, and a functional contact form with subtle slate borders and deep blue accents.',
                dir: 'elena_ai_portfolio'
            },
            'frontend-dev': {
                prompt: 'Create a clean, contemporary portfolio for Leo Thorne, Senior Frontend Architect & UI Engineer. Feature a light aesthetic with subtle shadows, interactive project gallery with filter tabs (Web Applications, Component Systems, Canvas Tools), technical stats counters, skill pill badges, and a smooth-scrolling sticky navigation bar with light/dark contrast.',
                dir: 'leo_frontend_portfolio'
            },
            'devops-cloud': {
                prompt: 'Design an ultra-clean, structured technical portfolio for Marcus Chen, Staff Site Reliability & Cloud Architect. Highlight core competencies in Kubernetes, Terraform, AWS, and Distributed Systems. Include architecture case studies, certification verification badges, high-availability uptime metrics, and direct contact options.',
                dir: 'marcus_cloud_portfolio'
            },
            'cybersecurity': {
                prompt: 'Build an elegant, high-contrast security researcher portfolio for Maya Lin, Systems Security Consultant & Cryptography Specialist. Feature a clean layout with monospace data accents, CVE disclosure timeline, research whitepaper list, penetration testing toolkit highlights, and verified contact links.',
                dir: 'maya_security_portfolio'
            },
            'minimal-executive': {
                prompt: 'Create a refined, minimalist executive portfolio for Julian Ross, VP of Engineering & Technical Advisor. Employ Swiss typography, crisp slate monochrome palette, leadership and architectural principles overview, advisory company highlights, and an executive contact card.',
                dir: 'julian_executive_portfolio'
            }
        }
    };

    // SVG icon templates
    const ICONS = {
        sun: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
        moon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
        check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
        alert: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        info: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        trash: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>'
    };

    // =========================================================
    // DOM Elements Cache
    // =========================================================
    const el = {
        // Header
        agentStatusBadge: document.getElementById('agent-status-badge'),
        agentStatusText: document.getElementById('agent-status-text'),
        headerModelName: document.getElementById('header-model-name'),
        sitesCountBadge: document.getElementById('sites-count-badge'),
        openGalleryBtn: document.getElementById('open-gallery-btn'),
        resetFormBtn: document.getElementById('reset-form-btn'),
        themeToggleBtn: document.getElementById('theme-toggle-btn'),

        // Mode Switcher
        tabModePrompt: document.getElementById('tab-mode-prompt'),
        tabModeWizard: document.getElementById('tab-mode-wizard'),
        sectionPromptMode: document.getElementById('section-prompt-mode'),
        sectionWizardMode: document.getElementById('section-wizard-mode'),

        // Prompt inputs
        promptName: document.getElementById('prompt-name'),
        promptTitle: document.getElementById('prompt-title'),
        promptInput: document.getElementById('prompt-input'),
        promptTargetDir: document.getElementById('prompt-target-dir'),

        // Wizard inputs
        wizardName: document.getElementById('wizard-name'),
        wizardTitle: document.getElementById('wizard-title'),
        wizardDir: document.getElementById('wizard-dir'),
        wizardBio: document.getElementById('wizard-bio'),
        wizardSkillsContainer: document.getElementById('wizard-skills-container'),
        skillInput: document.getElementById('skill-input'),
        addSkillBtn: document.getElementById('add-skill-btn'),
        wizardProjectsList: document.getElementById('wizard-projects-list'),
        addProjectBtn: document.getElementById('add-project-btn'),
        wizardEmail: document.getElementById('wizard-email'),
        wizardGithub: document.getElementById('wizard-github'),

        // Settings
        toggleSettingsBtn: document.getElementById('toggle-settings-btn'),
        accordionSettings: document.getElementById('accordion-settings'),
        mockModeToggle: document.getElementById('mock-mode-toggle'),
        settingModel: document.getElementById('setting-model'),
        customModelGroup: document.getElementById('custom-model-group'),
        settingCustomModel: document.getElementById('setting-custom-model'),
        settingApiKey: document.getElementById('setting-api-key'),
        settingBaseUrl: document.getElementById('setting-base-url'),
        settingTurns: document.getElementById('setting-turns'),
        turnsVal: document.getElementById('turns-val'),
        settingTemp: document.getElementById('setting-temp'),
        tempVal: document.getElementById('temp-val'),

        // Action
        generateBtn: document.getElementById('generate-btn'),
        btnLabel: document.getElementById('btn-label'),

        // Right Studio Tabs
        studioTabs: document.querySelectorAll('.studio-tab'),
        tabViews: document.querySelectorAll('.tab-view'),
        agentTabIndicator: document.getElementById('agent-tab-indicator'),
        previewDeviceActions: document.getElementById('preview-device-actions'),

        // Agent Stream View
        agentProgressBar: document.getElementById('agent-progress-bar'),
        agentThoughtCard: document.getElementById('agent-thought-card'),
        agentThoughtText: document.getElementById('agent-thought-text'),
        terminalLogs: document.getElementById('terminal-logs'),
        clearLogBtn: document.getElementById('clear-log-btn'),
        autoscrollToggleBtn: document.getElementById('autoscroll-toggle-btn'),
        readyBanner: document.getElementById('ready-banner'),
        readySiteDesc: document.getElementById('ready-site-desc'),
        viewPreviewBtn: document.getElementById('view-preview-btn'),
        readyExternalBtn: document.getElementById('ready-external-btn'),

        // Preview View
        previewSiteSelect: document.getElementById('preview-site-select'),
        previewUrlText: document.getElementById('preview-url-text'),
        copyPreviewUrlBtn: document.getElementById('copy-preview-url-btn'),
        deviceFrame: document.getElementById('device-frame'),
        previewIframe: document.getElementById('preview-iframe'),
        deviceBtns: document.querySelectorAll('.device-btn'),
        rotateDeviceBtn: document.getElementById('rotate-device-btn'),
        reloadPreviewBtn: document.getElementById('reload-preview-btn'),
        openNewTabBtn: document.getElementById('open-new-tab-btn'),

        // Code View
        codeFilesList: document.getElementById('code-files-list'),
        currentCodeFilename: document.getElementById('current-code-filename'),
        codeEditorTextarea: document.getElementById('code-editor-textarea'),
        copyCodeBtn: document.getElementById('copy-code-btn'),
        saveCodeBtn: document.getElementById('save-code-btn'),

        // Export View
        exportStatFiles: document.getElementById('export-stat-files'),
        exportStatSize: document.getElementById('export-stat-size'),
        exportStatDir: document.getElementById('export-stat-dir'),
        downloadZipBtn: document.getElementById('download-zip-btn'),

        // Gallery Modal
        galleryModal: document.getElementById('gallery-modal'),
        closeGalleryBtn: document.getElementById('close-gallery-btn'),
        gallerySitesGrid: document.getElementById('gallery-sites-grid'),

        // Toasts
        toastContainer: document.getElementById('toast-container')
    };

    // =========================================================
    // Initialization
    // =========================================================
    async function init() {
        setupEventListeners();
        renderSkills();
        renderProjects();
        await loadConfig();
        await loadSites();
    }

    // =========================================================
    // Configuration & Sites Loading
    // =========================================================
    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            if (!res.ok) throw new Error('Failed to load server configuration.');
            const data = await res.json();
            state.config = data;

            el.headerModelName.textContent = data.model || 'gpt-4o-mini';
            el.settingModel.value = data.model || 'gpt-4o-mini';

            if (data.default_name) {
                state.defaultName = data.default_name;
            }
            if (data.default_title) {
                state.defaultTitle = data.default_title;
            }

            // Fetch live models available directly from provider
            try {
                const mRes = await fetch('/api/models');
                if (mRes.ok) {
                    const mData = await mRes.json();
                    if (mData.models && mData.models.length > 0) {
                        el.settingModel.innerHTML = '';
                        const currentVal = data.model || '';
                        let matched = false;
                        mData.models.forEach(mid => {
                            const opt = document.createElement('option');
                            opt.value = mid;
                            opt.textContent = mid;
                            if (mid === currentVal) {
                                opt.selected = true;
                                matched = true;
                            }
                            el.settingModel.appendChild(opt);
                        });
                        if (!matched && el.settingModel.options.length > 0) {
                            el.settingModel.selectedIndex = 0;
                            data.model = el.settingModel.value;
                            el.headerModelName.textContent = data.model;
                        }
                        const customOpt = document.createElement('option');
                        customOpt.value = 'custom';
                        customOpt.textContent = 'Custom Model ID...';
                        el.settingModel.appendChild(customOpt);
                    }
                }
            } catch (mErr) {
                // Keep fallback options
            }

            // Auto-select mock mode if server has no OpenAI API key
            if (!data.has_api_key) {
                el.mockModeToggle.checked = true;
                showToast('No API key detected. Running in Mock Simulation Mode.', 'info');
            }
        } catch (err) {
            console.warn('Config load failed:', err);
        }
    }

    async function loadSites() {
        try {
            const res = await fetch('/api/sites');
            if (!res.ok) return;
            const data = await res.json();
            const sites = data.sites || [];
            state.sites = sites;
            el.sitesCountBadge.textContent = sites.length;

            if (el.previewSiteSelect) {
                el.previewSiteSelect.innerHTML = '';
                sites.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.id;
                    opt.textContent = `${s.dir_name} (${s.files_count} files)`;
                    if (s.id === state.currentSiteId) opt.selected = true;
                    el.previewSiteSelect.appendChild(opt);
                });
            }

            if (sites.length > 0) {
                const targetSite = (state.currentSiteId && sites.some(s => s.id === state.currentSiteId))
                    ? state.currentSiteId
                    : sites[0].id;
                selectSite(targetSite, false);
            }
        } catch (err) {
            console.error('Failed to load sites:', err);
        }
    }

    // =========================================================
    // Event Listeners Setup
    // =========================================================
    function setupEventListeners() {
        // Theme Switcher (Default to LIGHT)
        const savedTheme = localStorage.getItem('studio-theme') || 'light';
        document.body.setAttribute('data-theme', savedTheme);
        updateThemeToggleIcon(savedTheme);

        el.themeToggleBtn.addEventListener('click', () => {
            const current = document.body.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-theme', next);
            localStorage.setItem('studio-theme', next);
            updateThemeToggleIcon(next);
        });

        // Mode Switching
        el.tabModePrompt.addEventListener('click', () => switchMode('prompt'));
        el.tabModeWizard.addEventListener('click', () => switchMode('wizard'));

        // Preset Chips
        document.querySelectorAll('.preset-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const presetKey = chip.getAttribute('data-preset');
                const preset = state.presets[presetKey];
                if (preset) {
                    const currentName = el.promptName.value.trim() || state.defaultName || 'John Doe';
                    let tailoredPrompt = preset.prompt;
                    tailoredPrompt = tailoredPrompt.replace(/Dr\. Elena Vance|Leo Thorne|Marcus Chen|Maya Lin|Julian Ross/g, currentName);
                    el.promptInput.value = tailoredPrompt;
                    const slug = (el.promptName.value.trim() ? currentName : 'my').toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
                    el.promptTargetDir.value = `${slug}_portfolio`;
                    showToast(`Applied preset: ${chip.textContent.trim()}`, 'info');
                }
            });
        });

        // Prompt & Wizard Auto Dir Slugification
        el.promptName.addEventListener('input', () => {
            const name = el.promptName.value.trim();
            const slug = name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
            el.promptTargetDir.value = slug ? `${slug}_portfolio` : 'my_portfolio';
            if (el.wizardName && !el.wizardName.dataset.dirty) {
                el.wizardName.value = name;
                el.wizardDir.value = el.promptTargetDir.value;
            }
        });

        el.wizardName.addEventListener('input', () => {
            el.wizardName.dataset.dirty = 'true';
            const slug = el.wizardName.value.trim().toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
            el.wizardDir.value = slug ? `${slug}_portfolio` : 'my_portfolio';
        });

        // Wizard Skills
        el.addSkillBtn.addEventListener('click', addSkillFromInput);
        el.skillInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSkillFromInput();
            }
        });

        document.querySelectorAll('.quick-skill-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const skill = tag.getAttribute('data-skill');
                if (skill && !state.wizardSkills.includes(skill)) {
                    state.wizardSkills.push(skill);
                    renderSkills();
                }
            });
        });

        // Wizard Projects
        el.addProjectBtn.addEventListener('click', () => {
            state.wizardProjects.push({
                name: 'New Featured Project',
                tag: 'SYSTEMS',
                tech: 'Python, Docker',
                desc: 'Describe what this project achieves and its key technologies.'
            });
            renderProjects();
        });

        // Theme Selector Radio Cards
        document.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });
        });

        // Settings Accordion
        el.toggleSettingsBtn.addEventListener('click', () => {
            el.accordionSettings.classList.toggle('open');
        });

        // Model Selector
        el.settingModel.addEventListener('change', () => {
            el.customModelGroup.style.display = el.settingModel.value === 'custom' ? 'block' : 'none';
        });

        // Sliders
        el.settingTurns.addEventListener('input', () => el.turnsVal.textContent = el.settingTurns.value);
        el.settingTemp.addEventListener('input', () => el.tempVal.textContent = el.settingTemp.value);

        // Generate Action Button & Shortcut
        el.generateBtn.addEventListener('click', startGeneration);
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                startGeneration();
            }
        });

        // Right Studio Tabs
        el.studioTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                switchStudioTab(targetTab);
            });
        });

        // Terminal Actions
        el.clearLogBtn.addEventListener('click', () => {
            el.terminalLogs.innerHTML = '';
        });

        el.autoscrollToggleBtn.addEventListener('click', () => {
            state.autoscroll = !state.autoscroll;
            el.autoscrollToggleBtn.textContent = `Auto-scroll: ${state.autoscroll ? 'ON' : 'OFF'}`;
        });

        // Ready Banner Buttons
        el.viewPreviewBtn.addEventListener('click', () => switchStudioTab('preview'));

        // Device Switcher
        el.deviceBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                el.deviceBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.device = btn.getAttribute('data-device');
                applyDeviceFrame();
            });
        });

        el.rotateDeviceBtn.addEventListener('click', () => {
            state.isLandscape = !state.isLandscape;
            applyDeviceFrame();
        });

        el.reloadPreviewBtn.addEventListener('click', reloadPreview);

        // Site Switcher
        if (el.previewSiteSelect) {
            el.previewSiteSelect.addEventListener('change', () => {
                selectSite(el.previewSiteSelect.value, false);
            });
        }

        // URL Copy
        el.copyPreviewUrlBtn.addEventListener('click', () => {
            const text = el.previewUrlText.textContent;
            navigator.clipboard.writeText(text);
            showToast('Preview URL copied to clipboard.', 'success');
        });

        // Code Inspector
        el.copyCodeBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(el.codeEditorTextarea.value);
            showToast('Code copied to clipboard.', 'success');
        });

        el.saveCodeBtn.addEventListener('click', saveActiveFile);

        // Export View
        el.downloadZipBtn.addEventListener('click', () => {
            if (state.currentSiteId) {
                window.location.href = `/api/sites/${state.currentSiteId}/download`;
            }
        });

        // Sites Library Modal
        el.openGalleryBtn.addEventListener('click', openGallery);
        el.closeGalleryBtn.addEventListener('click', closeGallery);
        el.galleryModal.addEventListener('click', (e) => {
            if (e.target === el.galleryModal) closeGallery();
        });

        // Reset
        el.resetFormBtn.addEventListener('click', () => {
            el.promptInput.value = '';
            showToast('Reset form to blank.', 'info');
        });
    }

    function updateThemeToggleIcon(theme) {
        el.themeToggleBtn.innerHTML = theme === 'dark' ? ICONS.sun : ICONS.moon;
        el.themeToggleBtn.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
    }

    // =========================================================
    // Mode Switching
    // =========================================================
    function switchMode(mode) {
        state.mode = mode;
        if (mode === 'prompt') {
            el.tabModePrompt.classList.add('active');
            el.tabModeWizard.classList.remove('active');
            el.sectionPromptMode.classList.add('active');
            el.sectionWizardMode.classList.remove('active');
        } else {
            el.tabModePrompt.classList.remove('active');
            el.tabModeWizard.classList.add('active');
            el.sectionPromptMode.classList.remove('active');
            el.sectionWizardMode.classList.add('active');
        }
    }

    // =========================================================
    // Studio Tabs Switching
    // =========================================================
    function switchStudioTab(tabName) {
        state.activeTab = tabName;
        el.studioTabs.forEach(t => {
            t.classList.toggle('active', t.getAttribute('data-tab') === tabName);
        });
        el.tabViews.forEach(v => {
            v.classList.toggle('active', v.id === `view-${tabName}`);
        });

        el.previewDeviceActions.style.display = tabName === 'preview' ? 'flex' : 'none';

        if (tabName === 'preview') {
            if (state.currentSiteId) {
                ensurePreviewLoaded(state.currentSiteId);
            }
        } else if (tabName === 'code') {
            if (state.currentSiteId) {
                loadSiteFilesForInspector(state.currentSiteId);
            }
        } else if (tabName === 'export') {
            updateExportDetails();
        }
    }

    // =========================================================
    // Skills & Projects Handlers
    // =========================================================
    function addSkillFromInput() {
        const val = el.skillInput.value.trim();
        if (val && !state.wizardSkills.includes(val)) {
            state.wizardSkills.push(val);
            renderSkills();
            el.skillInput.value = '';
        }
    }

    function renderSkills() {
        el.wizardSkillsContainer.innerHTML = '';
        state.wizardSkills.forEach((skill, idx) => {
            const chip = document.createElement('div');
            chip.className = 'skill-chip';
            chip.innerHTML = `<span>${skill}</span> <span class="skill-chip-remove" data-idx="${idx}">&times;</span>`;
            chip.querySelector('.skill-chip-remove').addEventListener('click', () => {
                state.wizardSkills.splice(idx, 1);
                renderSkills();
            });
            el.wizardSkillsContainer.appendChild(chip);
        });
    }

    function renderProjects() {
        el.wizardProjectsList.innerHTML = '';
        state.wizardProjects.forEach((proj, idx) => {
            const item = document.createElement('div');
            item.className = 'project-item-card';
            item.innerHTML = `
                <div class="project-item-header">
                    <input type="text" class="proj-name-input" value="${proj.name}" placeholder="Project Title">
                    <button type="button" class="project-item-delete" title="Remove">&times;</button>
                </div>
                <div class="form-row" style="margin-bottom: 0.45rem;">
                    <input type="text" class="proj-tag-input" value="${proj.tag}" placeholder="Category (e.g. SYSTEMS)">
                    <input type="text" class="proj-tech-input" value="${proj.tech}" placeholder="Technologies">
                </div>
                <textarea class="proj-desc-input" rows="2" placeholder="Brief summary...">${proj.desc}</textarea>
            `;

            item.querySelector('.proj-name-input').addEventListener('input', (e) => proj.name = e.target.value);
            item.querySelector('.proj-tag-input').addEventListener('input', (e) => proj.tag = e.target.value);
            item.querySelector('.proj-tech-input').addEventListener('input', (e) => proj.tech = e.target.value);
            item.querySelector('.proj-desc-input').addEventListener('input', (e) => proj.desc = e.target.value);
            item.querySelector('.project-item-delete').addEventListener('click', () => {
                state.wizardProjects.splice(idx, 1);
                renderProjects();
            });

            el.wizardProjectsList.appendChild(item);
        });
    }

    // =========================================================
    // Agent Execution & Streaming
    // =========================================================
    async function startGeneration() {
        if (state.isGenerating) return;

        let payload = {};
        let dirName = '';

        const fallbackName = state.defaultName || 'John Doe';
        const fallbackTitle = state.defaultTitle || 'Full-Stack Engineer';

        if (state.mode === 'wizard') {
            const name = el.wizardName.value.trim() || el.promptName.value.trim() || fallbackName;
            const title = el.wizardTitle.value.trim() || el.promptTitle.value.trim() || fallbackTitle;
            dirName = el.wizardDir.value.trim() || `${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_portfolio`;

            const selectedThemeEl = document.querySelector('input[name="wizard-theme"]:checked');
            const theme = selectedThemeEl ? selectedThemeEl.value : 'Modern Clean Light Minimalist';

            payload = {
                mode: 'wizard',
                name,
                title,
                dir_name: dirName,
                wizard_data: {
                    name,
                    title,
                    directory_name: dirName,
                    bio: el.wizardBio.value.trim(),
                    skills: state.wizardSkills,
                    projects: state.wizardProjects.map(p => ({
                        name: p.name,
                        tag: p.tag,
                        tags: p.tech.split(',').map(s => s.trim()).filter(Boolean),
                        description: p.desc
                    })),
                    theme,
                    contact_email: el.wizardEmail.value.trim(),
                    github: el.wizardGithub.value.trim(),
                }
            };
        } else {
            const promptText = el.promptInput.value.trim();
            if (!promptText) {
                showToast('Please enter a description for your website.', 'error');
                el.promptInput.focus();
                return;
            }
            const name = el.promptName.value.trim() || el.wizardName.value.trim() || fallbackName;
            const title = el.promptTitle.value.trim() || el.wizardTitle.value.trim() || fallbackTitle;
            dirName = el.promptTargetDir.value.trim() || `${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_portfolio`;
            payload = {
                mode: 'prompt',
                name,
                title,
                prompt: promptText,
                dir_name: dirName
            };
        }

        // Engine Options
        payload.mock = el.mockModeToggle.checked;
        const selectedModel = el.settingModel.value === 'custom'
            ? (el.settingCustomModel.value.trim() || 'gpt-4o-mini')
            : el.settingModel.value;
        payload.model = selectedModel;

        if (el.settingApiKey.value.trim()) {
            payload.api_key = el.settingApiKey.value.trim();
        }
        if (el.settingBaseUrl.value.trim()) {
            payload.base_url = el.settingBaseUrl.value.trim();
        } else if (payload.api_key && payload.api_key.startsWith('gsk_')) {
            payload.base_url = 'https://api.groq.com/openai/v1';
        } else if (selectedModel.startsWith('llama-') || selectedModel.startsWith('llama3')) {
            if (!state.config?.base_url || state.config.base_url.includes('api.openai.com')) {
                payload.base_url = 'https://api.groq.com/openai/v1';
            }
        }
        payload.max_turns = parseInt(el.settingTurns.value);
        payload.temperature = parseFloat(el.settingTemp.value);

        // Update UI state
        setGeneratingState(true);
        resetProgressAndLogs();
        switchStudioTab('agent');
        logMessage(`[INIT] Starting portfolio generation task for directory: generated_sites/${dirName}`, 'system');

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || 'Server rejected generation request.');
            }

            const data = await res.json();
            state.currentJobId = data.job_id;
            state.currentSiteId = data.site_dir;

            connectEventStream(data.job_id);
        } catch (err) {
            setGeneratingState(false);
            logMessage(`[ERROR] Failed to start generation: ${err.message}`, 'error');
            showToast(err.message, 'error');
        }
    }

    function setGeneratingState(isGen) {
        state.isGenerating = isGen;
        el.generateBtn.disabled = isGen;
        el.generateBtn.classList.toggle('loading', isGen);
        el.btnLabel.textContent = isGen ? 'Generating Portfolio...' : 'Generate Portfolio Website';

        el.agentStatusBadge.classList.toggle('running', isGen);
        el.agentStatusText.textContent = isGen ? 'Working' : 'Ready';
        el.agentTabIndicator.classList.toggle('active', isGen);
    }

    function resetProgressAndLogs() {
        el.agentProgressBar.style.width = '5%';
        document.querySelectorAll('.milestone').forEach(m => m.className = 'milestone');
        document.getElementById('ms-init').classList.add('active');
        el.agentThoughtCard.style.display = 'none';
        el.readyBanner.style.display = 'none';
    }

    function connectEventStream(jobId) {
        if (state.eventSource) {
            state.eventSource.close();
        }

        const sse = new EventSource(`/api/jobs/${jobId}/events`);
        state.eventSource = sse;

        sse.onmessage = (event) => {
            try {
                const ev = JSON.parse(event.data);
                handleAgentEvent(ev);
            } catch (err) {
                console.error('Failed to parse SSE payload:', err);
            }
        };

        sse.onerror = (err) => {
            console.warn('SSE stream disconnected:', err);
            sse.close();
            state.eventSource = null;
            if (state.isGenerating) {
                checkJobStatus(jobId);
            }
        };
    }

    async function checkJobStatus(jobId) {
        try {
            const res = await fetch(`/api/jobs/${jobId}`);
            if (res.ok) {
                const job = await res.json();
                if (job.status === 'completed' || job.status === 'failed') {
                    onGenerationSuccess(job);
                }
            }
        } catch (e) {
            setGeneratingState(false);
        }
    }

    function handleAgentEvent(ev) {
        const type = ev.type;
        const msg = ev.message;
        const data = ev.data || {};

        if (type === 'stream_close') {
            if (state.eventSource) state.eventSource.close();
            return;
        }

        if (type === 'start') {
            updateMilestone('ms-init', 'done');
            updateMilestone('ms-dir', 'active');
            logMessage(`[START] ${msg}`, 'system');
        } else if (type === 'step') {
            const turn = data.turn || 1;
            const maxTurns = data.max_turns || 25;
            const pct = Math.min(95, Math.max(10, Math.round((turn / maxTurns) * 100)));
            el.agentProgressBar.style.width = `${pct}%`;
            logMessage(`[TURN ${turn}/${maxTurns}] ${msg}`, 'step');
        } else if (type === 'tool_call') {
            const tool = data.tool;
            const args = data.args;
            logMessage(`  [TOOL] ${tool} (${args})`, 'tool-call');

            if (tool === 'create_directory') {
                updateMilestone('ms-dir', 'done');
                updateMilestone('ms-html', 'active');
            } else if (tool === 'write_file') {
                if (args.includes('index.html')) {
                    updateMilestone('ms-html', 'done');
                    updateMilestone('ms-css', 'active');
                } else if (args.includes('style.css')) {
                    updateMilestone('ms-css', 'done');
                    updateMilestone('ms-js', 'active');
                } else if (args.includes('script.js')) {
                    updateMilestone('ms-js', 'done');
                    updateMilestone('ms-verify', 'active');
                }
            } else if (tool === 'list_files') {
                updateMilestone('ms-verify', 'active');
            }
        } else if (type === 'tool_result') {
            const resPreview = data.result.length > 180 ? data.result.slice(0, 180) + '...' : data.result;
            logMessage(`  [RESULT] ${resPreview}`, 'tool-result');
        } else if (type === 'agent_message') {
            el.agentThoughtCard.style.display = 'block';
            el.agentThoughtText.textContent = data.content;
            logMessage(`[REASONING] ${data.content.slice(0, 160)}${data.content.length > 160 ? '...' : ''}`, 'agent');
        } else if (type === 'complete') {
            el.agentProgressBar.style.width = '100%';
            document.querySelectorAll('.milestone').forEach(m => m.className = 'milestone done');
            logMessage(`[SUCCESS] ${msg}`, 'success');
            onGenerationSuccess(data);
        } else if (type === 'failed') {
            logMessage(`[ERROR] ${data.error || msg}`, 'error');
            showToast(`Generation failed: ${data.error || msg}`, 'error');
            setGeneratingState(false);
        }
    }

    function updateMilestone(id, status) {
        const elM = document.getElementById(id);
        if (elM) {
            elM.className = `milestone ${status}`;
        }
    }

    function logMessage(text, category = 'system') {
        const line = document.createElement('div');
        line.className = `log-line log-${category}`;
        line.textContent = text;
        el.terminalLogs.appendChild(line);

        if (state.autoscroll) {
            el.terminalLogs.scrollTop = el.terminalLogs.scrollHeight;
        }
    }

    async function onGenerationSuccess(data) {
        setGeneratingState(false);
        const siteDir = data.site_dir || state.currentSiteId;
        state.currentSiteId = siteDir;

        el.readyBanner.style.display = 'flex';
        el.readySiteDesc.textContent = `Portfolio '${siteDir}' was built and is active in the workspace (${data.created_files ? data.created_files.length : 3} files).`;
        el.readyExternalBtn.href = `/preview/${siteDir}/`;

        await loadSites();
        ensurePreviewLoaded(siteDir);
        showToast(`Portfolio '${siteDir}' created & hosted locally.`, 'success');
    }

    // =========================================================
    // Preview Management
    // =========================================================
    function ensurePreviewLoaded(siteId) {
        const url = `/preview/${siteId}/`;
        const fullLocalUrl = `${window.location.origin}${url}`;

        el.previewUrlText.textContent = fullLocalUrl;
        el.openNewTabBtn.href = url;
        el.readyExternalBtn.href = url;

        el.previewIframe.src = url;
    }

    function reloadPreview() {
        if (state.currentSiteId) {
            const url = `/preview/${state.currentSiteId}/?t=${Date.now()}`;
            el.previewIframe.src = url;
            showToast('Preview refreshed.', 'info');
        }
    }

    function applyDeviceFrame() {
        const frame = el.deviceFrame;
        frame.className = `device-frame ${state.device}`;

        if (state.device === 'mobile') {
            if (state.isLandscape) {
                frame.style.width = '667px';
                frame.style.height = '375px';
            } else {
                frame.style.width = '375px';
                frame.style.height = '667px';
            }
        } else if (state.device === 'tablet') {
            if (state.isLandscape) {
                frame.style.width = '1024px';
                frame.style.height = '768px';
            } else {
                frame.style.width = '768px';
                frame.style.height = '100%';
            }
        } else {
            frame.style.width = '';
            frame.style.height = '';
        }
    }

    // =========================================================
    // Code Inspector
    // =========================================================
    async function loadSiteFilesForInspector(siteId) {
        try {
            const res = await fetch(`/api/sites/${siteId}/files`);
            if (!res.ok) return;
            const data = await res.json();
            const files = data.files || [];

            el.codeFilesList.innerHTML = '';
            files.forEach(f => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = `file-item-btn ${f.path === state.activeCodeFile ? 'active' : ''}`;
                btn.innerHTML = `<span class="file-badge-tag">${getFileBadge(f.path)}</span> <span>${f.path}</span>`;
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.file-item-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    loadCodeFile(siteId, f.path);
                });
                el.codeFilesList.appendChild(btn);
            });

            if (files.length > 0) {
                const targetPath = files.some(f => f.path === state.activeCodeFile) ? state.activeCodeFile : files[0].path;
                loadCodeFile(siteId, targetPath);
            }
        } catch (err) {
            console.error('Failed to load site files:', err);
        }
    }

    async function loadCodeFile(siteId, filePath) {
        state.activeCodeFile = filePath;
        el.currentCodeFilename.textContent = filePath;
        try {
            const res = await fetch(`/api/sites/${siteId}/file?path=${encodeURIComponent(filePath)}`);
            if (res.ok) {
                const data = await res.json();
                el.codeEditorTextarea.value = data.content || '';
            }
        } catch (err) {
            console.error('Failed to load file content:', err);
        }
    }

    async function saveActiveFile() {
        if (!state.currentSiteId || !state.activeCodeFile) return;
        const newContent = el.codeEditorTextarea.value;

        try {
            const res = await fetch(`/api/sites/${state.currentSiteId}/file`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: state.activeCodeFile,
                    content: newContent
                })
            });

            if (res.ok) {
                showToast(`Saved '${state.activeCodeFile}' and updated preview.`, 'success');
                reloadPreview();
            } else {
                throw new Error('Save failed');
            }
        } catch (err) {
            showToast(`Failed to save: ${err.message}`, 'error');
        }
    }

    function getFileBadge(name) {
        if (name.endsWith('.html')) return 'HTML';
        if (name.endsWith('.css')) return 'CSS';
        if (name.endsWith('.js')) return 'JS';
        return 'FILE';
    }

    // =========================================================
    // Export View
    // =========================================================
    async function updateExportDetails() {
        if (!state.currentSiteId) return;
        try {
            const res = await fetch(`/api/sites/${state.currentSiteId}/files`);
            if (res.ok) {
                const data = await res.json();
                const files = data.files || [];
                const totalBytes = files.reduce((acc, f) => acc + (f.size || 0), 0);
                el.exportStatFiles.textContent = files.length;
                el.exportStatSize.textContent = `${(totalBytes / 1024).toFixed(1)} KB`;
                el.exportStatDir.textContent = state.currentSiteId;
            }
        } catch (err) {
            console.error(err);
        }
    }

    // =========================================================
    // Sites Gallery Modal
    // =========================================================
    function openGallery() {
        renderGallerySites();
        el.galleryModal.style.display = 'flex';
    }

    function closeGallery() {
        el.galleryModal.style.display = 'none';
    }

    function renderGallerySites() {
        el.gallerySitesGrid.innerHTML = '';
        if (state.sites.length === 0) {
            el.gallerySitesGrid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1;">No websites found in workspace. Generate your first portfolio.</p>';
            return;
        }

        state.sites.forEach(site => {
            const card = document.createElement('div');
            card.className = 'site-card-item';
            const dateStr = site.mtime ? new Date(site.mtime * 1000).toLocaleDateString() : '';

            card.innerHTML = `
                <div class="site-card-title">${site.name}</div>
                <div class="site-card-meta">${site.dir_name} &bull; ${site.files_count} files &bull; ${dateStr}</div>
                <div class="site-card-actions">
                    <button type="button" class="site-card-btn primary preview-site-btn">Preview</button>
                    <a href="${site.preview_url}" target="_blank" class="site-card-btn">Open Tab</a>
                    <a href="/api/sites/${site.id}/download" class="site-card-btn">ZIP</a>
                    <button type="button" class="site-card-btn danger delete-site-btn" title="Delete">${ICONS.trash}</button>
                </div>
            `;

            card.querySelector('.preview-site-btn').addEventListener('click', () => {
                selectSite(site.id, true);
                closeGallery();
            });

            card.querySelector('.delete-site-btn').addEventListener('click', async () => {
                if (confirm(`Delete '${site.id}'?`)) {
                    await deleteSite(site.id);
                }
            });

            el.gallerySitesGrid.appendChild(card);
        });
    }

    function selectSite(siteId, switchTab = true) {
        state.currentSiteId = siteId;
        if (el.previewSiteSelect) {
            el.previewSiteSelect.value = siteId;
        }
        ensurePreviewLoaded(siteId);
        if (state.activeTab === 'code') {
            loadSiteFilesForInspector(siteId);
        } else if (state.activeTab === 'export') {
            updateExportDetails();
        }
        if (switchTab) {
            switchStudioTab('preview');
        }
    }

    async function deleteSite(siteId) {
        try {
            const res = await fetch(`/api/sites/${siteId}`, { method: 'DELETE' });
            if (res.ok) {
                showToast(`Deleted '${siteId}'`, 'info');
                await loadSites();
                renderGallerySites();
            }
        } catch (err) {
            showToast('Failed to delete site', 'error');
        }
    }

    // =========================================================
    // Toast Notifications
    // =========================================================
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const iconSvg = type === 'success' ? ICONS.check : (type === 'error' ? ICONS.alert : ICONS.info);
        toast.innerHTML = `<span>${iconSvg}</span> <span>${message}</span>`;
        el.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.25s ease';
            setTimeout(() => toast.remove(), 250);
        }, 3500);
    }

    // Initialize application
    init();
});
