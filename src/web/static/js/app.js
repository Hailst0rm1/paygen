// Paygen Web GUI - Main JavaScript

// Global state
let recipes = {};
let selectedRecipe = null;
let categories = {};
let activeEffectivenessFilters = new Set();
let activePlatformFilters = new Set();
let selectedVersion = null; // Track version for generation (null = latest)

// Notification popup
function showNotificationPopup(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadRecipes();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Header buttons
    document.getElementById('obfuscate-ps-btn').addEventListener('click', showObfuscatePsModal);
    document.getElementById('history-btn').addEventListener('click', showHistory);
    document.getElementById('settings-btn').addEventListener('click', showSettings);
    document.getElementById('refresh-btn').addEventListener('click', () => loadRecipes(true));
    
    // Effectiveness filter pills
    document.querySelectorAll('.filter-pill[data-effectiveness]').forEach(pill => {
        pill.addEventListener('click', function() {
            const effectiveness = this.dataset.effectiveness;
            
            // Toggle this filter on/off
            if (activeEffectivenessFilters.has(effectiveness)) {
                activeEffectivenessFilters.delete(effectiveness);
                this.classList.remove('active');
            } else {
                activeEffectivenessFilters.add(effectiveness);
                this.classList.add('active');
            }
            
            // Re-render with current search query
            const searchInput = document.getElementById('recipe-search');
            renderCategories(searchInput ? searchInput.value : '');
        });
    });
    
    // Platform filter pills
    document.querySelectorAll('.filter-pill[data-platform]').forEach(pill => {
        pill.addEventListener('click', function() {
            const platform = this.dataset.platform;
            
            // Toggle this filter on/off
            if (activePlatformFilters.has(platform)) {
                activePlatformFilters.delete(platform);
                this.classList.remove('active');
            } else {
                activePlatformFilters.add(platform);
                this.classList.add('active');
            }
            
            // Re-render with current search query
            const searchInput = document.getElementById('recipe-search');
            renderCategories(searchInput ? searchInput.value : '');
        });
    });
    
    // Fullscreen toggle for code preview
    const fullscreenToggle = document.getElementById('fullscreen-toggle');
    const codePreviewPanel = document.getElementById('code-preview-panel');
    const fullscreenIcon = document.getElementById('fullscreen-icon');
    
    if (fullscreenToggle && codePreviewPanel && fullscreenIcon) {
        fullscreenToggle.addEventListener('click', () => {
            codePreviewPanel.classList.toggle('fullscreen');
        });
    }
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            // Reset PS obfuscation modal to main view on close
            if (modal && modal.id === 'obfuscate-ps-modal') {
                showPsObfMainView();
            }
            modal.classList.remove('active');
        });
    });
    
    // Parameter modal buttons
    document.getElementById('cancel-generate-btn').addEventListener('click', function() {
        document.getElementById('param-modal').classList.remove('active');
    });
    
    document.getElementById('confirm-generate-btn').addEventListener('click', generatePayload);
    
    // Build modal close button
    const closeBuildBtn = document.getElementById('close-build-btn');
    if (closeBuildBtn) {
        closeBuildBtn.addEventListener('click', function() {
            document.getElementById('build-modal').classList.remove('active');
        });
    }
    
    // History modal buttons
    const closeHistoryBtn = document.getElementById('close-history-btn');
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', function() {
            document.getElementById('history-modal').classList.remove('active');
        });
    }
    
    // Clear history button handler is set dynamically in showHistory/showHistoryDetail
    // Don't add a static event listener here
    
    // PowerShell Obfuscator modal buttons
    const closeObfuscatePsBtn = document.getElementById('close-obfuscate-ps-btn');
    if (closeObfuscatePsBtn) {
        closeObfuscatePsBtn.addEventListener('click', function() {
            showPsObfMainView();
            document.getElementById('obfuscate-ps-modal').classList.remove('active');
        });
    }
    
    const obfuscatePsGenerateBtn = document.getElementById('obfuscate-ps-generate-btn');
    if (obfuscatePsGenerateBtn) {
        obfuscatePsGenerateBtn.addEventListener('click', generateObfuscatedPs);
    }
    
    const obfuscatePsCopyBtn = document.getElementById('obfuscate-ps-copy-btn');
    if (obfuscatePsCopyBtn) {
        obfuscatePsCopyBtn.addEventListener('click', copyObfuscatedPs);
    }

    // Download button for PS obfuscator
    const obfuscatePsDownloadBtn = document.getElementById('obfuscate-ps-download-btn');
    if (obfuscatePsDownloadBtn) {
        obfuscatePsDownloadBtn.addEventListener('click', downloadObfuscatedPs);
    }

    // File input for PS obfuscator
    const obfuscatePsFileInput = document.getElementById('obfuscate-ps-file-input');
    if (obfuscatePsFileInput) {
        obfuscatePsFileInput.addEventListener('change', handlePsFileUpload);
    }

    // Path input for PS obfuscator
    const obfuscatePsFilePath = document.getElementById('obfuscate-ps-file-path');
    if (obfuscatePsFilePath) {
        // Load file when Enter is pressed in path input
        obfuscatePsFilePath.addEventListener('keydown', async function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                await loadPsFileFromPath();
            }
        });
        // Also add a blur event to load when focus leaves the field
        obfuscatePsFilePath.addEventListener('blur', async function() {
            const path = obfuscatePsFilePath.value.trim();
            if (path && path !== currentLoadedPath) {
                await loadPsFileFromPath();
            }
        });
    }

    // Cradle toggle for PS obfuscator
    const obfuscatePsCradleToggle = document.getElementById('obfuscate-ps-cradle-toggle');
    if (obfuscatePsCradleToggle) {
        obfuscatePsCradleToggle.addEventListener('change', function() {
            const container = document.getElementById('obfuscate-ps-cradle-options');
            if (container) {
                container.style.display = obfuscatePsCradleToggle.checked ? 'block' : 'none';
            }
        });
    }

    // Drag and drop for PS obfuscator
    const obfuscatePsDropzone = document.getElementById('obfuscate-ps-dropzone');
    if (obfuscatePsDropzone) {
        obfuscatePsDropzone.addEventListener('dragover', handlePsDragOver);
        obfuscatePsDropzone.addEventListener('dragleave', handlePsDragLeave);
        obfuscatePsDropzone.addEventListener('drop', handlePsDrop);
    }
    
    // Settings modal buttons
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            saveSettings();
        });
    }
    
    // Close modals on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
}

// Load recipes from API
async function loadRecipes(showNotification = false) {
    try {
        // Show loading indicator on refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        const originalContent = refreshBtn.innerHTML;
        if (showNotification) {
            refreshBtn.innerHTML = '⟳';
            refreshBtn.style.animation = 'spin 0.5s linear';
        }
        
        const response = await fetch('/api/recipes');
        const data = await response.json();
        
        categories = data.categories;
        recipes = {};
        
        // Flatten recipes for easier access
        Object.keys(categories).forEach(category => {
            categories[category].forEach(recipe => {
                const key = `${category}::${recipe.name}`;
                recipes[key] = recipe;
            });
        });
        
        // Update header info
        document.getElementById('recipe-count').textContent = `Recipes: ${data.total_recipes}`;
        document.getElementById('category-count').textContent = `Categories: ${data.total_categories}`;
        
        // Render categories panel
        renderCategories();
        
        // If a recipe was selected, reload its details
        if (selectedRecipe) {
            const category = selectedRecipe.category;
            const name = selectedRecipe.name;
            // Re-select the recipe to refresh its details
            await selectRecipe(category, name);
        }
        
        // Show success notification
        if (showNotification) {
            refreshBtn.innerHTML = originalContent;
            refreshBtn.style.animation = '';
            showNotificationPopup(`✓ Refreshed: ${data.total_recipes} recipes in ${data.total_categories} categories`, 'success');
        }
    } catch (error) {
        console.error('Failed to load recipes:', error);
        document.getElementById('categories-panel').innerHTML = 
            '<div class="loading">Failed to load recipes. Please refresh.</div>';
        if (showNotification) {
            const refreshBtn = document.getElementById('refresh-btn');
            refreshBtn.innerHTML = '⟳';
            refreshBtn.style.animation = '';
            showNotificationPopup('✗ Failed to refresh recipes', 'error');
        }
    }
}

// Render categories and recipes
function renderCategories(filterQuery = '') {
    const container = document.getElementById('categories-container');
    if (!container) return;
    
    let html = '';
    
    // Filter recipes by search query and effectiveness
    let filteredCategories = {};
    
    Object.keys(categories).forEach(categoryName => {
        const matchingRecipes = categories[categoryName].filter(recipe => {
            // Check if recipe matches search query
            // Search in both name and description for more comprehensive results
            let matchesSearch = true;
            if (filterQuery) {
                const queryLower = filterQuery.toLowerCase();
                const nameLower = recipe.name.toLowerCase();
                const descLower = (recipe.description || '').toLowerCase();
                
                // Split query into words to support partial matching of multi-word searches
                const queryWords = queryLower.split(/\s+/).filter(w => w.length > 0);
                
                // Check if all query words are found in either name or description
                matchesSearch = queryWords.every(word => 
                    nameLower.includes(word) || descLower.includes(word)
                );
            }
            
            // Check if recipe matches effectiveness filter
            // If no filters are active, show all recipes
            const matchesEffectiveness = activeEffectivenessFilters.size === 0 || 
                                        activeEffectivenessFilters.has(recipe.effectiveness.toLowerCase());
            
            // Check if recipe matches platform filter
            // If no platform filters are active, show all recipes
            // If recipe has no platform specified, it works on all platforms (always show it)
            // If recipe has a platform, only show if it matches the filter
            const matchesPlatform = activePlatformFilters.size === 0 || 
                                   !recipe.platform || 
                                   activePlatformFilters.has(recipe.platform);
            
            return matchesSearch && matchesEffectiveness && matchesPlatform;
        });
        
        if (matchingRecipes.length > 0) {
            filteredCategories[categoryName] = matchingRecipes;
        }
    });
    
    // Sort categories with Misc and Examples at the bottom
    const sortedCategories = Object.keys(filteredCategories).sort((a, b) => {
        const aLower = a.toLowerCase();
        const bLower = b.toLowerCase();
        const aSpecial = aLower === 'misc' || aLower === 'examples';
        const bSpecial = bLower === 'misc' || bLower === 'examples';
        
        if (aSpecial && !bSpecial) return 1;
        if (!aSpecial && bSpecial) return -1;
        if (aSpecial && bSpecial) {
            // Examples before Misc
            if (aLower === 'examples') return -1;
            if (bLower === 'examples') return 1;
        }
        return a.localeCompare(b);
    });
    
    sortedCategories.forEach(categoryName => {
        const categoryRecipes = filteredCategories[categoryName];
        
        // Sort recipes by effectiveness: HIGH -> MEDIUM -> LOW
        const effectivenessOrder = { 'high': 1, 'medium': 2, 'low': 3 };
        const sortedRecipes = categoryRecipes.sort((a, b) => {
            const aOrder = effectivenessOrder[a.effectiveness.toLowerCase()] || 4;
            const bOrder = effectivenessOrder[b.effectiveness.toLowerCase()] || 4;
            return aOrder - bOrder;
        });
        
        html += `
            <div class="category">
                <div class="category-header" onclick="toggleCategory(this)">
                    <span class="category-toggle">▼</span>
                    <span>${categoryName}</span>
                </div>
                <div class="recipe-list">
                    ${sortedRecipes.map(recipe => `
                        <div class="recipe-item" 
                             data-category="${recipe.category}" 
                             data-name="${recipe.name}"
                             onclick="selectRecipe('${recipe.category}', '${recipe.name}')">
                            <div class="recipe-item-name">${recipe.name}</div>
                            <div class="recipe-item-effectiveness effectiveness-${recipe.effectiveness.toLowerCase()}">
                                ${recipe.effectiveness.toUpperCase()}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Setup search input event listener if not already set
    const searchInput = document.getElementById('recipe-search');
    if (searchInput && !searchInput.dataset.listenerAdded) {
        searchInput.dataset.listenerAdded = 'true';
        
        searchInput.addEventListener('input', (e) => {
            renderCategories(e.target.value);
        });
        
        // Focus search on '/' key
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                const activeElement = document.activeElement;
                if (activeElement.tagName !== 'INPUT' && activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    searchInput.focus();
                }
            }
        });
        
        // Clear search on Escape
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                renderCategories('');
                searchInput.blur();
            }
        });
    }
}

// Toggle category expansion
function toggleCategory(header) {
    const recipeList = header.nextElementSibling;
    const toggle = header.querySelector('.category-toggle');
    
    if (recipeList.style.display === 'none') {
        recipeList.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        recipeList.style.display = 'none';
        toggle.textContent = '▶';
    }
}

// Select a recipe
async function selectRecipe(category, name) {
    // Fetch full recipe details with resolved parameters
    try {
        const response = await fetch(`/api/recipe/${encodeURIComponent(category)}/${encodeURIComponent(name)}`);
        const recipe = await response.json();
        
        if (recipe.error) {
            console.error('Failed to load recipe:', recipe.error);
            return;
        }
        
        selectedRecipe = recipe;
        selectedVersion = null; // Reset to latest version
    } catch (error) {
        console.error('Failed to fetch recipe details:', error);
        return;
    }
    
    // Update selected state in UI
    document.querySelectorAll('.recipe-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const recipeItem = document.querySelector(
        `.recipe-item[data-category="${category}"][data-name="${name}"]`
    );
    if (recipeItem) {
        recipeItem.classList.add('selected');
    }
    
    // Render recipe details
    renderRecipeDetails(selectedRecipe);
    
    // Load and render code preview
    await loadCodePreview(category, name);
}

// Render recipe details in middle panel
function renderRecipeDetails(recipe) {
    const panel = document.getElementById('recipe-details');
    
    let html = '<div class="recipe-meta">';
    
    // Name and Category
    html += `<div class="recipe-name">${escapeHtml(recipe.name)}</div>`;
    const displayCategory = recipe.category || 'Misc';
    html += `<div class="recipe-category">Category: ${escapeHtml(displayCategory)}</div>`;
    if (selectedVersion !== null) {
        html += `<div class="version-badge">Using version ${selectedVersion}</div>`;
    }
    html += '<div class="separator"></div>';
    
    // Effectiveness
    html += '<div class="section-header">Effectiveness:</div>';
    html += `
        <div class="effectiveness-value">
            <span class="recipe-item-effectiveness effectiveness-${recipe.effectiveness.toLowerCase()}">
                ${recipe.effectiveness.toUpperCase()}
            </span>
        </div>
    `;
    html += '<div class="separator"></div>';
    
    // Platform
    if (recipe.platform) {
        html += '<div class="section-header">Platform:</div>';
        const platformIcons = {
            'Windows': '🪟',
            'Linux': '🐧',
            'macOS': '🍎'
        };
        const icon = platformIcons[recipe.platform] || '';
        html += `
            <div class="platform-value">
                <span class="platform-badge platform-${recipe.platform.toLowerCase()}">
                    ${icon} ${escapeHtml(recipe.platform)}
                </span>
            </div>
        `;
        html += '<div class="separator"></div>';
    }
    
    // Description
    html += '<div class="section-header">Description:</div>';
    const formattedDescription = recipe.description.split('\n').map(line => 
        `<div class="description-line">${escapeHtml(line) || '&nbsp;'}</div>`
    ).join('');
    html += `<div class="description-content">${formattedDescription}</div>`;
    html += '<div class="separator"></div>';
    
    // MITRE ATT&CK
    if (recipe.mitre_tactic || recipe.mitre_technique) {
        html += '<div class="section-header">MITRE ATT&CK:</div>';
        if (recipe.mitre_tactic) {
            html += `<div class="mitre-item"><span class="mitre-label">Tactic:</span> <span class="mitre-value">${escapeHtml(recipe.mitre_tactic)}</span></div>`;
        }
        if (recipe.mitre_technique) {
            html += `<div class="mitre-item"><span class="mitre-label">Technique:</span> <span class="mitre-value">${escapeHtml(recipe.mitre_technique)}</span></div>`;
        }
        html += '<div class="separator"></div>';
    }
    
    // Artifacts
    if (recipe.artifacts && recipe.artifacts.length > 0) {
        html += '<div class="section-header">Artifacts:</div>';
        html += '<ul class="artifacts-list">';
        recipe.artifacts.forEach(artifact => {
            html += `<li class="artifact-item">${escapeHtml(artifact)}</li>`;
        });
        html += '</ul>';
        html += '<div class="separator"></div>';
    }
    
    // Parameters
    if (recipe.parameters && recipe.parameters.length > 0) {
        html += '<div class="section-header">Parameters:</div>';
        recipe.parameters.forEach(param => {
            const reqMarker = param.required ? '<span class="param-required">*</span>' : '<span class="param-optional"> </span>';
            
            // Determine parameter color based on type
            let typeColor = 'var(--blue)';
            if (param.type === 'ip') typeColor = 'var(--teal)';
            else if (param.type === 'port') typeColor = 'var(--peach)';
            else if (param.type === 'path') typeColor = 'var(--yellow)';
            else if (param.type === 'bool') typeColor = 'var(--lavender)';
            else if (param.type === 'choice') typeColor = 'var(--mauve)';
            
            html += `
                <div class="param-detail">
                    ${reqMarker} <span class="param-name-detail">${escapeHtml(param.name)}</span>
                    <span class="param-type-detail" style="color: ${typeColor};">[${escapeHtml(param.type)}]</span>
            `;
            
            if (param.default !== undefined) {
                html += ` <span class="param-default-detail">= ${escapeHtml(String(param.default))}</span>`;
            }
            
            html += '</div>';
            
            if (param.description) {
                html += `<div class="param-description-detail">${escapeHtml(param.description)}</div>`;
            }
        });
        html += '<div class="separator"></div>';
    }
    
    // Preprocessing steps
    if (recipe.preprocessing && recipe.preprocessing.length > 0) {
        html += '<div class="section-header">Preprocessing Steps:</div>';
        recipe.preprocessing.forEach((step, idx) => {
            // Use name field first, fallback to script/command, then type
            let preprocessorName = step.name || step.script || step.command || step.type;
            let preprocessorType = step.type || (step.script ? 'script' : (step.command ? 'command' : 'unknown'));
            
            html += `
                <div class="preprocessing-step">
                    ${idx + 1}. <span class="preprocessing-name">${escapeHtml(preprocessorName)}</span>
                    <span class="preprocessing-type">(${preprocessorType})</span>
                </div>
            `;
            
            if (step.key) {
                html += `<div class="preprocessing-key">Key: ${escapeHtml(step.key)}</div>`;
            }
        });
        html += '<div class="separator"></div>';
    }
    
    // Compiler info (if template-based with compilation)
    if (recipe.is_template_based && recipe.output.compile && recipe.output.compile.enabled) {
        const command = recipe.output.compile.command || '';
        const compiler = command.split(' ')[0] || 'unknown';
        html += `
            <div class="compiler-row">
                <span class="section-header">Compiler:</span>
                <span class="compiler-name">${escapeHtml(compiler)}</span>
            </div>
            <div class="separator"></div>
        `;
    }
    
    // Launch Instructions with Markdown rendering
    if (recipe.launch_instructions) {
        html += '<div class="section-header">Launch Instructions:</div>';
        html += '<div class="launch-instructions-markdown" id="launch-instructions-md"></div>';
    }
    
    html += '</div>'; // Close recipe-meta

    // Generate button (pinned to bottom)
    html += `<div style="flex-shrink:0;">`;
    html += `
        <button class="btn btn-generate" onclick="showParameterForm()">
            <span class="btn-icon">🚀</span> Generate Payload
        </button>
    `;
    html += `</div>`;
    
    panel.innerHTML = html;

    // Render Markdown for launch instructions
    if (recipe.launch_instructions) {
        renderLaunchInstructions(recipe.launch_instructions);
    }

    // Update header action buttons
    updateRecipeHeaderActions(recipe);
}

function updateRecipeHeaderActions(recipe) {
    const actions = document.getElementById('recipe-header-actions');
    const versionsBtn = document.getElementById('versions-recipe-btn');
    const versionsBtnLabel = document.getElementById('versions-btn-label');
    if (!actions) return;

    if (recipe) {
        actions.style.display = '';
        if (recipe.version_count && recipe.version_count > 0) {
            versionsBtn.style.display = '';
            versionsBtn.title = `Version History (${recipe.version_count})`;
        } else {
            versionsBtn.style.display = 'none';
        }
    } else {
        actions.style.display = 'none';
    }
}

// Render launch instructions as Markdown with copy buttons
function renderLaunchInstructions(instructions, containerId = 'launch-instructions-md') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Configure marked to use Prism for syntax highlighting
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && Prism.languages[lang]) {
                return Prism.highlight(code, Prism.languages[lang], lang);
            }
            return code;
        },
        breaks: true
    });
    
    // Render markdown
    const rendered = marked.parse(instructions);
    container.innerHTML = rendered;
    
    // Add copy buttons to all code blocks
    container.querySelectorAll('pre > code').forEach((codeBlock, idx) => {
        const pre = codeBlock.parentElement;
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.onclick = function() {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyBtn.innerHTML = '✓ Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '📋 Copy';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        };
        
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        wrapper.appendChild(copyBtn);
        
        // Apply syntax highlighting
        Prism.highlightElement(codeBlock);
    });
}

// Add copy buttons to code blocks within a container
function addCopyButtonsToCodeBlocks(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.querySelectorAll('pre > code').forEach((codeBlock) => {
        const pre = codeBlock.parentElement;
        
        // Skip if already has a wrapper (already processed)
        if (pre.parentElement.classList.contains('code-block-wrapper')) {
            return;
        }
        
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        wrapper.style.position = 'relative';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.style.position = 'absolute';
        copyBtn.style.top = '0.5rem';
        copyBtn.style.right = '0.5rem';
        copyBtn.style.padding = '0.25rem 0.5rem';
        copyBtn.style.background = 'var(--surface0)';
        copyBtn.style.color = 'var(--text)';
        copyBtn.style.border = '1px solid var(--overlay0)';
        copyBtn.style.borderRadius = '4px';
        copyBtn.style.cursor = 'pointer';
        copyBtn.style.fontSize = '0.8rem';
        
        copyBtn.onclick = function() {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyBtn.innerHTML = '✓ Copied!';
                copyBtn.style.color = 'var(--green)';
                setTimeout(() => {
                    copyBtn.innerHTML = '📋 Copy';
                    copyBtn.style.color = 'var(--text)';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        };
        
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        wrapper.appendChild(copyBtn);
    });
}

// Load and render code preview
async function loadCodePreview(category, name) {
    const panel = document.getElementById('code-preview');
    
    try {
        const response = await fetch(`/api/recipe/${encodeURIComponent(category)}/${encodeURIComponent(name)}/code`);
        const data = await response.json();
        
        let codeElement;
        
        if (data.type === 'command') {
            // For commands, show only the type without language
            panel.innerHTML = `
                <div class="code-container">
                    <div class="code-header">
                        <span>Type: <span class="code-language">command</span></span>
                    </div>
                    <pre class="line-numbers"><code class="language-bash" id="code-content"></code></pre>
                </div>
            `;
            codeElement = document.getElementById('code-content');
            codeElement.textContent = data.code;
        } else {
            // For templates, show both type and language
            panel.innerHTML = `
                <div class="code-container">
                    <div class="code-header">
                        <span>Type: <span class="code-language">${data.type}</span></span>
                        <span>Language: <span class="code-language">${data.language}</span></span>
                    </div>
                    <pre class="line-numbers"><code class="language-${data.language}" id="code-content"></code></pre>
                </div>
            `;
            codeElement = document.getElementById('code-content');
            codeElement.textContent = data.code;
        }
        
        // Apply syntax highlighting with Prism
        Prism.highlightAll();
    } catch (error) {
        console.error('Failed to load code preview:', error);
        panel.innerHTML = '<div class="placeholder"><p>Failed to load code preview</p></div>';
    }
}

// Show parameter form
async function showParameterForm() {
    if (!selectedRecipe) return;
    
    // Load AMSI bypasses
    let amsiBypasses = [];
    try {
        const response = await fetch('/api/amsi-bypasses');
        const data = await response.json();
        amsiBypasses = data.bypasses || [];
    } catch (error) {
        console.error('Failed to load AMSI bypasses:', error);
    }
    
    // Load PS obfuscation methods
    let psObfMethods = [];
    try {
        const response = await fetch('/api/ps-obfuscation-methods');
        const data = await response.json();
        psObfMethods = data.methods || [];
    } catch (error) {
        console.error('Failed to load PS obfuscation methods:', error);
    }
    
    // Load PS cradles
    let psCradles = {ps1: [], exe: [], dll: []};
    try {
        const response = await fetch('/api/ps-cradles');
        const data = await response.json();
        psCradles = data.cradles || {ps1: [], exe: [], dll: []};
    } catch (error) {
        console.error('Failed to load PS cradles:', error);
    }
    
    const container = document.getElementById('param-form-container');
    let html = '';
    
    // Add preprocessing options section first
    const preprocessingOptions = selectedRecipe.preprocessing?.filter(p => p.type === 'option') || [];
    const shellcodeSteps = selectedRecipe.preprocessing?.filter(p => p.type === 'shellcode') || [];
    
    // Handle shellcode preprocessing steps
    if (shellcodeSteps.length > 0) {
        html += `
            <div class="param-form-section-title">Shellcode Configuration</div>
        `;
        
        // Load shellcode configurations
        let shellcodes = [];
        try {
            const response = await fetch('/api/shellcodes');
            const data = await response.json();
            shellcodes = data.shellcodes || [];
        } catch (error) {
            console.error('Failed to load shellcode configurations:', error);
        }
        
        for (let shellcodeIdx = 0; shellcodeIdx < shellcodeSteps.length; shellcodeIdx++) {
            const shellcodeStep = shellcodeSteps[shellcodeIdx];
            const outputVar = shellcodeStep.output_var || 'raw_shellcode';
            
            html += `
                <div class="param-form-item">
                    <label class="param-form-label">
                        ${shellcodeStep.name || 'Shellcode Generation Method'}
                        <span class="param-type">[shellcode]</span>
                    </label>
                    <select class="param-form-select shellcode-selection" 
                            data-output-var="${outputVar}" 
                            id="shellcode-select-${shellcodeIdx}">
                        <option value="">-- Select Shellcode Method --</option>
            `;
            
            shellcodes.forEach((shellcode, idx) => {
                html += `<option value="${escapeHtml(shellcode.name)}" ${idx === 0 ? 'selected' : ''}>${escapeHtml(shellcode.name)}</option>`;
            });
            
            html += `
                    </select>
                    <div class="param-form-description">Select the shellcode generation method</div>
                </div>
                
                <!-- Container for shellcode-specific parameters -->
                <div id="shellcode-params-${shellcodeIdx}" class="shellcode-params-container">
                </div>
            `;
        }
        
        if (preprocessingOptions.length > 0) {
            html += `<div class="param-form-separator"></div>`;
        }
    }
    
    // Handle preprocessing options
    if (preprocessingOptions.length > 0) {
        html += `
            <div class="param-form-section-title">Preprocessing Options</div>
        `;
        
        preprocessingOptions.forEach((optionStep, idx) => {
            html += `
                <div class="param-form-item">
                    <label class="param-form-label">
                        ${optionStep.name}
                        <span class="param-type">[option]</span>
                    </label>
                    <select class="param-form-select preprocessing-option" data-option-name="${optionStep.name}" id="preprocessing-option-${idx}">
            `;
            
            optionStep.options.forEach((opt, optIdx) => {
                // First option is selected by default
                html += `<option value="${optIdx}" ${optIdx === 0 ? 'selected' : ''}>${opt.name}</option>`;
            });
            
            html += `
                    </select>
                    <div class="param-form-description">Select the method to use for this preprocessing step</div>
                </div>
            `;
        });
    }
    
    // Add regular parameters
    if (selectedRecipe.parameters && selectedRecipe.parameters.length > 0) {
        // Only add separator if preprocessing options exist
        if (preprocessingOptions.length > 0) {
            html += `<div class="param-form-separator"></div>`;
        }
        html += `
            <div class="param-form-section-title">Parameters</div>
        `;
        
        selectedRecipe.parameters.forEach(param => {
            // Determine if this parameter is conditional
            const requiredFor = param['required_for'];
            const isConditional = requiredFor !== undefined;
            const isRequired = param.required || false;
            
            // Build data attributes for conditional parameters
            let dataAttrs = '';
            let containerStyle = '';
            if (isConditional) {
                dataAttrs = `data-required-for="${requiredFor}"`;
                // Hide conditional parameters by default, will be shown based on selection
                containerStyle = 'style="display: none;"';
            }
            
            html += `
                <div class="param-form-item param-conditional" ${dataAttrs} ${containerStyle}>
                    <label class="param-form-label">
                        ${param.name}
                        ${isRequired || isConditional ? '<span class="param-required">*</span>' : ''}
                        <span class="param-type">[${param.type}]</span>
                    </label>
            `;
            
            if (param.type === 'choice' && param.choices) {
                html += `
                    <select class="param-form-select" data-param="${param.name}">
                        <option value="">-- Select --</option>
                        ${param.choices.map(c => `
                            <option value="${c}" ${param.default === c ? 'selected' : ''}>${c}</option>
                        `).join('')}
                    </select>
                `;
            } else if (param.type === 'bool') {
                html += `
                    <select class="param-form-select" data-param="${param.name}">
                        <option value="true" ${param.default === true ? 'selected' : ''}>True</option>
                        <option value="false" ${param.default === false ? 'selected' : ''}>False</option>
                    </select>
                `;
            } else {
                // Process default value with template substitution
                let defaultVal = param.default !== undefined ? param.default : '';
                defaultVal = processParameterDefault(defaultVal, param.name);
                
                // Check if this is an lhost parameter and use default from settings
                if (param.name.toLowerCase() === 'lhost') {
                    const settingsLhost = getDefaultLhost();
                    if (settingsLhost) {
                        defaultVal = settingsLhost;
                    }
                }
                
                html += `
                    <input type="text" 
                           class="param-form-input" 
                           data-param="${param.name}"
                           value="${defaultVal}"
                           placeholder="${param.description || param.name}">
                `;
            }
            
            if (param.description) {
                html += `<div class="param-form-description">${param.description}</div>`;
            }
            
            html += `<div class="param-form-error" id="error-${param.name}"></div>`;
            html += '</div>';
        });
    } else {
        html += '<p>This recipe has no configurable parameters.</p>';
    }
    
    // Add language-specific options section (for PowerShell obfuscation)
    const outputType = selectedRecipe.output?.type || 'template';
    if (outputType === 'template') {
        const templatePath = selectedRecipe.output?.template || '';
        const templateExt = (selectedRecipe.output?.template_ext || '').toLowerCase();
        // Check template_ext first (inline templates), then fall back to file path
        const isPS1 = templateExt === '.ps1' || templatePath.toLowerCase().endsWith('.ps1');
        const isCS = templateExt === '.cs' || templatePath.toLowerCase().endsWith('.cs');
        
        if (isPS1) {
            html += `
                <div class="param-form-separator"></div>
                <div class="param-form-section-title">Language Specific Options</div>
                
                <!-- AMSI Bypass -->
                <div class="param-form-item">
                    <label class="param-form-checkbox-label">
                        <input type="checkbox" id="ps-amsi-bypass" class="param-form-checkbox">
                        Insert AMSI bypass
                    </label>
                    <div class="param-form-description">Inject AMSI bypass at the beginning of the script</div>
                </div>
                <div class="param-form-item" id="ps-amsi-method-container" style="display: none;">
                    <label class="param-form-label">
                        Bypass Method
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="ps-amsi-method">
                        ${amsiBypasses.map(bypass => `<option value="${bypass.name}">${bypass.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">AMSI bypass method to inject</div>
                </div>
                <div class="param-form-item" id="ps-amsi-obf-container" style="display: none;">
                    <label class="param-form-label">
                        Obfuscate AMSI Bypass
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="ps-amsi-obf-method">
                        <option value="">None</option>
                        ${psObfMethods.map(method => `<option value="${method.name}">${method.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">Obfuscation to apply to AMSI bypass code</div>
                </div>
                
                <!-- Script Obfuscation -->
                <div class="param-form-item">
                    <label class="param-form-checkbox-label">
                        <input type="checkbox" id="ps-obfuscate" class="param-form-checkbox">
                        Obfuscate PowerShell script
                    </label>
                    <div class="param-form-description">Apply obfuscation using psobf to evade detection</div>
                </div>
                <div class="param-form-item" id="ps-obfuscate-level-container">
                    <label class="param-form-label">
                        Obfuscation Method
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="ps-obfuscate-level">
                        ${psObfMethods.map((method, idx) => `<option value="${method.name}" ${idx === 0 ? 'selected' : ''}>${method.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">Obfuscation method to apply to the script</div>
                </div>
                
                <!-- PowerShell Cradle -->
                <div class="param-form-item">
                    <label class="param-form-checkbox-label">
                        <input type="checkbox" id="ps-cradle" class="param-form-checkbox">
                        Add download cradle
                    </label>
                    <div class="param-form-description">Generate a download cradle for launching the payload</div>
                </div>
                <div class="param-form-item" id="ps-cradle-method-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Method
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="ps-cradle-method">
                        ${psCradles.ps1.map(cradle => `<option value="${cradle.name}">${cradle.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">PowerShell cradle method for downloading</div>
                </div>
                <div class="param-form-item" id="ps-cradle-obf-container" style="display: none;">
                    <label class="param-form-label">
                        Obfuscate Cradle
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="ps-cradle-obf-method">
                        <option value="">None</option>
                        ${psObfMethods.map(method => `<option value="${method.name}">${method.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">Obfuscation to apply to the cradle</div>
                </div>
                <div class="param-form-item" id="ps-cradle-lhost-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Listener Host
                        <span class="param-required">*</span>
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="ps-cradle-lhost" placeholder="192.168.1.100" data-cradle-required="true">
                    <div class="param-form-description">IP address or hostname for the download cradle URL</div>
                    <div class="param-form-error" id="error-ps-cradle-lhost"></div>
                </div>
                <div class="param-form-item" id="ps-cradle-lport-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Listener Port
                        <span class="param-required">*</span>
                        <span class="param-type">[number]</span>
                    </label>
                    <input type="number" class="param-form-input" id="ps-cradle-lport" value="80" min="1" max="65535" data-cradle-required="true">
                    <div class="param-form-description">Port for the download cradle URL (80=http://, 443=https://, other=http://host:port/)</div>
                    <div class="param-form-error" id="error-ps-cradle-lport"></div>
                </div>
                <div class="param-form-item" id="ps-cradle-manual-override-container" style="display: none;">
                    <label class="param-form-label">
                        <input type="checkbox" id="ps-cradle-manual-override">
                        Manual Override
                        <span class="param-type">[bool]</span>
                    </label>
                    <div class="param-form-description">Manually specify namespace/class/entry point instead of auto-extracting from compiled payload (cannot be used with C# obfuscation)</div>
                </div>
                <div class="param-form-item" id="ps-cradle-auto-detected-container" style="display: none;">
                    <div class="param-form-description" style="color: #4a9eff; font-style: italic;">
                        ℹ️ Namespace, class, and entry point will be automatically extracted from the compiled payload
                    </div>
                </div>
                <div class="param-form-item" id="ps-cradle-namespace-container" style="display: none;">
                    <label class="param-form-label">
                        .NET Namespace
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="ps-cradle-namespace" placeholder="MyNamespace">
                    <div class="param-form-description">.NET namespace for assembly loading (e.g., MyApp)</div>
                </div>
                <div class="param-form-item" id="ps-cradle-class-container" style="display: none;">
                    <label class="param-form-label">
                        .NET Class
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="ps-cradle-class" placeholder="Program">
                    <div class="param-form-description">.NET class name containing the entry point (e.g., Program)</div>
                </div>
                <div class="param-form-item" id="ps-cradle-entry-point-container" style="display: none;">
                    <label class="param-form-label">
                        Entry Point
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="ps-cradle-entry-point" placeholder="Main">
                    <div class="param-form-description">Entry point method/function name (e.g., Main, DllMain)</div>
                </div>
                <div class="param-form-item" id="ps-cradle-args-container" style="display: none;">
                    <label class="param-form-label">
                        Arguments
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="ps-cradle-args" placeholder="arg1 arg2">
                    <div class="param-form-description">Command-line arguments (space-separated)</div>
                </div>
            `;
            
            // Add event listener logic for checkbox toggles (will be added after DOM update)
            setTimeout(() => {
                const amsiCheckbox = document.getElementById('ps-amsi-bypass');
                const amsiContainer = document.getElementById('ps-amsi-method-container');
                const amsiObfContainer = document.getElementById('ps-amsi-obf-container');
                const amsiMethodSelect = document.getElementById('ps-amsi-method');
                
                const obfCheckbox = document.getElementById('ps-obfuscate');
                const levelContainer = document.getElementById('ps-obfuscate-level-container');
                
                const cradleCheckbox = document.getElementById('ps-cradle');
                const cradleContainer = document.getElementById('ps-cradle-method-container');
                const cradleObfContainer = document.getElementById('ps-cradle-obf-container');
                const cradleMethodSelect = document.getElementById('ps-cradle-method');
                
                // AMSI bypass toggle
                if (amsiCheckbox && amsiContainer) {
                    const updateAmsiVisibility = () => {
                        const checked = amsiCheckbox.checked;
                        amsiContainer.style.display = checked ? 'block' : 'none';
                        
                        // Show obfuscation option if AMSI is enabled and method allows obfuscation
                        if (checked && amsiMethodSelect) {
                            const selectedMethod = amsiBypasses.find(b => b.name === amsiMethodSelect.value);
                            amsiObfContainer.style.display = (selectedMethod && !selectedMethod.no_obf) ? 'block' : 'none';
                        } else {
                            amsiObfContainer.style.display = 'none';
                        }
                    };
                    
                    amsiCheckbox.addEventListener('change', updateAmsiVisibility);
                    if (amsiMethodSelect) {
                        amsiMethodSelect.addEventListener('change', updateAmsiVisibility);
                    }
                    updateAmsiVisibility();
                }
                
                // Script obfuscation toggle
                if (obfCheckbox && levelContainer) {
                    const updateLevelVisibility = () => {
                        levelContainer.style.display = obfCheckbox.checked ? 'block' : 'none';
                    };
                    
                    obfCheckbox.addEventListener('change', updateLevelVisibility);
                    updateLevelVisibility();
                }
                
                // Cradle toggle
                if (cradleCheckbox && cradleContainer) {
                    const lhostContainer = document.getElementById('ps-cradle-lhost-container');
                    const lportContainer = document.getElementById('ps-cradle-lport-container');
                    const manualOverrideContainer = document.getElementById('ps-cradle-manual-override-container');
                    const autoDetectedContainer = document.getElementById('ps-cradle-auto-detected-container');
                    const manualOverrideCheckbox = document.getElementById('ps-cradle-manual-override');
                    const namespaceContainer = document.getElementById('ps-cradle-namespace-container');
                    const classContainer = document.getElementById('ps-cradle-class-container');
                    const entryPointContainer = document.getElementById('ps-cradle-entry-point-container');
                    const argsContainer = document.getElementById('ps-cradle-args-container');
                    
                    const updateCradleVisibility = () => {
                        const checked = cradleCheckbox.checked;
                        cradleContainer.style.display = checked ? 'block' : 'none';
                        
                        // Show lhost/lport fields when cradle is enabled
                        if (lhostContainer) {
                            lhostContainer.style.display = checked ? 'block' : 'none';
                            // Set default lhost from settings if empty
                            if (checked) {
                                const lhostInput = document.getElementById('ps-cradle-lhost');
                                if (lhostInput && !lhostInput.value) {
                                    const defaultLhost = getDefaultLhost();
                                    if (defaultLhost) {
                                        lhostInput.value = defaultLhost;
                                    }
                                }
                            }
                        }
                        if (lportContainer) lportContainer.style.display = checked ? 'block' : 'none';
                        
                        // Find selected cradle and show/hide fields based on what it uses
                        if (checked && cradleMethodSelect) {
                            const selectedCradle = psCradles.ps1.find(c => c.name === cradleMethodSelect.value);
                            
                            // Show obfuscation option if method allows obfuscation
                            cradleObfContainer.style.display = (selectedCradle && !selectedCradle.no_obf) ? 'block' : 'none';
                            
                            // Check if cradle uses any metadata fields
                            const usesMetadata = selectedCradle && (selectedCradle.uses_namespace || selectedCradle.uses_class || selectedCradle.uses_entry_point);
                            
                            // Check if C# obfuscation is enabled
                            const csObfEnabled = document.getElementById('obfuscate-cs-names')?.checked || false;
                            
                            // Show manual override checkbox only if metadata is needed and CS obfuscation is disabled
                            if (manualOverrideContainer) {
                                manualOverrideContainer.style.display = (usesMetadata && !csObfEnabled) ? 'block' : 'none';
                            }
                            
                            // If CS obfuscation is enabled, uncheck manual override
                            if (csObfEnabled && manualOverrideCheckbox) {
                                manualOverrideCheckbox.checked = false;
                            }
                            
                            // Determine if manual mode is active
                            const manualMode = manualOverrideCheckbox?.checked || false;
                            
                            // Show auto-detected message or manual fields based on mode
                            if (usesMetadata) {
                                if (manualMode) {
                                    // Show manual input fields
                                    if (autoDetectedContainer) autoDetectedContainer.style.display = 'none';
                                    if (namespaceContainer) namespaceContainer.style.display = selectedCradle.uses_namespace ? 'block' : 'none';
                                    if (classContainer) classContainer.style.display = selectedCradle.uses_class ? 'block' : 'none';
                                    if (entryPointContainer) entryPointContainer.style.display = selectedCradle.uses_entry_point ? 'block' : 'none';
                                } else {
                                    // Show auto-detected message, hide manual fields
                                    if (autoDetectedContainer) autoDetectedContainer.style.display = 'block';
                                    if (namespaceContainer) namespaceContainer.style.display = 'none';
                                    if (classContainer) classContainer.style.display = 'none';
                                    if (entryPointContainer) entryPointContainer.style.display = 'none';
                                }
                            } else {
                                // Cradle doesn't use metadata
                                if (manualOverrideContainer) manualOverrideContainer.style.display = 'none';
                                if (autoDetectedContainer) autoDetectedContainer.style.display = 'none';
                                if (namespaceContainer) namespaceContainer.style.display = 'none';
                                if (classContainer) classContainer.style.display = 'none';
                                if (entryPointContainer) entryPointContainer.style.display = 'none';
                            }
                            
                            // Args field is always shown/hidden based on cradle requirements
                            if (argsContainer) argsContainer.style.display = selectedCradle?.uses_args ? 'block' : 'none';
                        } else {
                            cradleObfContainer.style.display = 'none';
                            if (namespaceContainer) namespaceContainer.style.display = 'none';
                            if (classContainer) classContainer.style.display = 'none';
                            if (entryPointContainer) entryPointContainer.style.display = 'none';
                            if (argsContainer) argsContainer.style.display = 'none';
                        }
                        
                        // Revalidate when visibility changes
                        validateAllParameters();
                    };
                    
                    cradleCheckbox.addEventListener('change', updateCradleVisibility);
                    if (cradleMethodSelect) {
                        cradleMethodSelect.addEventListener('change', updateCradleVisibility);
                    }
                    
                    // Manual override checkbox listener
                    if (manualOverrideCheckbox) {
                        manualOverrideCheckbox.addEventListener('change', updateCradleVisibility);
                    }
                    
                    // C# obfuscation checkbox listener (to disable manual override when enabled)
                    const csObfCheckbox = document.getElementById('obfuscate-cs-names');
                    if (csObfCheckbox) {
                        csObfCheckbox.addEventListener('change', updateCradleVisibility);
                    }
                    
                    updateCradleVisibility();
                    
                    // Add validation listeners for cradle fields
                    const psCradleLhostInput = document.getElementById('ps-cradle-lhost');
                    const psCradleLportInput = document.getElementById('ps-cradle-lport');
                    if (psCradleLhostInput) {
                        psCradleLhostInput.addEventListener('input', () => {
                            validateAllParameters();
                        });
                        psCradleLhostInput.addEventListener('blur', () => {
                            validateAllParameters();
                        });
                    }
                    if (psCradleLportInput) {
                        psCradleLportInput.addEventListener('input', () => {
                            validateAllParameters();
                        });
                        psCradleLportInput.addEventListener('blur', () => {
                            validateAllParameters();
                        });
                    }
                }
            }, 0);
        } else if (isCS) {
            // Determine cradle type based on output file extension
            const outputFile = selectedRecipe.parameters?.find(p => p.name === 'output_file')?.default || '';
            const isExe = outputFile.toLowerCase().endsWith('.exe');
            const isDll = outputFile.toLowerCase().endsWith('.dll');
            const cradleType = isExe ? 'exe' : isDll ? 'dll' : 'exe'; // Default to exe
            const availableCradles = cradleType === 'dll' ? psCradles.dll : psCradles.exe;
            
            html += `
                <div class="param-form-separator"></div>
                <div class="param-form-section-title">Language Specific Options</div>
                <div class="param-form-item">
                    <label class="param-form-checkbox-label">
                        <input type="checkbox" id="cs-obfuscate-names" class="param-form-checkbox">
                        Obfuscate function/variable names
                    </label>
                    <div class="param-form-description">Replace function and variable names with innocuous identifiers (forest, lake, var1, etc.)</div>
                </div>
                
                <!-- C# Cradle -->
                <div class="param-form-item">
                    <label class="param-form-checkbox-label">
                        <input type="checkbox" id="cs-cradle" class="param-form-checkbox">
                        Add download cradle
                    </label>
                    <div class="param-form-description">Generate a download cradle for launching the payload</div>
                </div>
                <div class="param-form-item" id="cs-cradle-method-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Method (${cradleType.toUpperCase()})
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="cs-cradle-method">
                        ${availableCradles.map(cradle => `<option value="${cradle.name}">${cradle.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">PowerShell cradle method for downloading ${cradleType.toUpperCase()}</div>
                </div>
                <div class="param-form-item" id="cs-cradle-obf-container" style="display: none;">
                    <label class="param-form-label">
                        Obfuscate Cradle
                        <span class="param-type">[choice]</span>
                    </label>
                    <select class="param-form-select" id="cs-cradle-obf-method">
                        <option value="">None</option>
                        ${psObfMethods.map(method => `<option value="${method.name}">${method.name}</option>`).join('')}
                    </select>
                    <div class="param-form-description">Obfuscation to apply to the cradle</div>
                </div>
                <div class="param-form-item" id="cs-cradle-lhost-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Listener Host
                        <span class="param-required">*</span>
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="cs-cradle-lhost" placeholder="192.168.1.100" data-cradle-required="true">
                    <div class="param-form-description">IP address or hostname for the download cradle URL</div>
                    <div class="param-form-error" id="error-cs-cradle-lhost"></div>
                </div>
                <div class="param-form-item" id="cs-cradle-lport-container" style="display: none;">
                    <label class="param-form-label">
                        Cradle Listener Port
                        <span class="param-required">*</span>
                        <span class="param-type">[number]</span>
                    </label>
                    <input type="number" class="param-form-input" id="cs-cradle-lport" value="80" min="1" max="65535" data-cradle-required="true">
                    <div class="param-form-description">Port for the download cradle URL (80=http://, 443=https://, other=http://host:port/)</div>
                    <div class="param-form-error" id="error-cs-cradle-lport"></div>
                </div>
                <div class="param-form-item" id="cs-cradle-manual-override-container" style="display: none;">
                    <label class="param-form-label">
                        <input type="checkbox" id="cs-cradle-manual-override">
                        Manual Override
                        <span class="param-type">[bool]</span>
                    </label>
                    <div class="param-form-description">Manually specify namespace/class/entry point instead of auto-extracting from compiled payload (cannot be used with C# obfuscation)</div>
                </div>
                <div class="param-form-item" id="cs-cradle-auto-detected-container" style="display: none;">
                    <div class="param-form-description" style="color: #4a9eff; font-style: italic;">
                        ℹ️ Namespace, class, and entry point will be automatically extracted from the compiled payload
                    </div>
                </div>
                <div class="param-form-item" id="cs-cradle-namespace-container" style="display: none;">
                    <label class="param-form-label">
                        .NET Namespace
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="cs-cradle-namespace" placeholder="MyNamespace">
                    <div class="param-form-description">.NET namespace for assembly loading (e.g., MyApp)</div>
                </div>
                <div class="param-form-item" id="cs-cradle-class-container" style="display: none;">
                    <label class="param-form-label">
                        .NET Class
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="cs-cradle-class" placeholder="Program">
                    <div class="param-form-description">.NET class name containing the entry point (e.g., Program)</div>
                </div>
                <div class="param-form-item" id="cs-cradle-entry-point-container" style="display: none;">
                    <label class="param-form-label">
                        Entry Point
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="cs-cradle-entry-point" placeholder="Main">
                    <div class="param-form-description">Entry point method/function name (e.g., Main, DllMain)</div>
                </div>
                <div class="param-form-item" id="cs-cradle-args-container" style="display: none;">
                    <label class="param-form-label">
                        Arguments
                        <span class="param-type">[string]</span>
                    </label>
                    <input type="text" class="param-form-input" id="cs-cradle-args" placeholder="arg1 arg2">
                    <div class="param-form-description">Command-line arguments (space-separated)</div>
                </div>
            `;
            
            // Add event listener for C# cradle toggle
            setTimeout(() => {
                const cradleCheckbox = document.getElementById('cs-cradle');
                const cradleContainer = document.getElementById('cs-cradle-method-container');
                const cradleObfContainer = document.getElementById('cs-cradle-obf-container');
                const cradleMethodSelect = document.getElementById('cs-cradle-method');
                
                if (cradleCheckbox && cradleContainer) {
                    const lhostContainer = document.getElementById('cs-cradle-lhost-container');
                    const lportContainer = document.getElementById('cs-cradle-lport-container');
                    const manualOverrideContainer = document.getElementById('cs-cradle-manual-override-container');
                    const autoDetectedContainer = document.getElementById('cs-cradle-auto-detected-container');
                    const manualOverrideCheckbox = document.getElementById('cs-cradle-manual-override');
                    const namespaceContainer = document.getElementById('cs-cradle-namespace-container');
                    const classContainer = document.getElementById('cs-cradle-class-container');
                    const entryPointContainer = document.getElementById('cs-cradle-entry-point-container');
                    const argsContainer = document.getElementById('cs-cradle-args-container');
                    
                    const updateCradleVisibility = () => {
                        const checked = cradleCheckbox.checked;
                        cradleContainer.style.display = checked ? 'block' : 'none';
                        
                        // Show lhost/lport fields when cradle is enabled
                        if (lhostContainer) {
                            lhostContainer.style.display = checked ? 'block' : 'none';
                            // Set default lhost from settings if empty
                            if (checked) {
                                const lhostInput = document.getElementById('cs-cradle-lhost');
                                if (lhostInput && !lhostInput.value) {
                                    const defaultLhost = getDefaultLhost();
                                    if (defaultLhost) {
                                        lhostInput.value = defaultLhost;
                                    }
                                }
                            }
                        }
                        if (lportContainer) lportContainer.style.display = checked ? 'block' : 'none';
                        
                        // Find selected cradle and show/hide fields based on what it uses
                        if (checked && cradleMethodSelect) {
                            const selectedCradle = availableCradles.find(c => c.name === cradleMethodSelect.value);
                            
                            // Show obfuscation option if method allows obfuscation
                            cradleObfContainer.style.display = (selectedCradle && !selectedCradle.no_obf) ? 'block' : 'none';
                            
                            // Check if cradle uses any metadata fields
                            const usesMetadata = selectedCradle && (selectedCradle.uses_namespace || selectedCradle.uses_class || selectedCradle.uses_entry_point);
                            
                            // Check if C# obfuscation is enabled
                            const csObfEnabled = document.getElementById('obfuscate-cs-names')?.checked || false;
                            
                            // Show manual override checkbox only if metadata is needed and CS obfuscation is disabled
                            if (manualOverrideContainer) {
                                manualOverrideContainer.style.display = (usesMetadata && !csObfEnabled) ? 'block' : 'none';
                            }
                            
                            // If CS obfuscation is enabled, uncheck manual override
                            if (csObfEnabled && manualOverrideCheckbox) {
                                manualOverrideCheckbox.checked = false;
                            }
                            
                            // Determine if manual mode is active
                            const manualMode = manualOverrideCheckbox?.checked || false;
                            
                            // Show auto-detected message or manual fields based on mode
                            if (usesMetadata) {
                                if (manualMode) {
                                    // Show manual input fields
                                    if (autoDetectedContainer) autoDetectedContainer.style.display = 'none';
                                    if (namespaceContainer) namespaceContainer.style.display = selectedCradle.uses_namespace ? 'block' : 'none';
                                    if (classContainer) classContainer.style.display = selectedCradle.uses_class ? 'block' : 'none';
                                    if (entryPointContainer) entryPointContainer.style.display = selectedCradle.uses_entry_point ? 'block' : 'none';
                                } else {
                                    // Show auto-detected message, hide manual fields
                                    if (autoDetectedContainer) autoDetectedContainer.style.display = 'block';
                                    if (namespaceContainer) namespaceContainer.style.display = 'none';
                                    if (classContainer) classContainer.style.display = 'none';
                                    if (entryPointContainer) entryPointContainer.style.display = 'none';
                                }
                            } else {
                                // Cradle doesn't use metadata
                                if (manualOverrideContainer) manualOverrideContainer.style.display = 'none';
                                if (autoDetectedContainer) autoDetectedContainer.style.display = 'none';
                                if (namespaceContainer) namespaceContainer.style.display = 'none';
                                if (classContainer) classContainer.style.display = 'none';
                                if (entryPointContainer) entryPointContainer.style.display = 'none';
                            }
                            
                            // Args field is always shown/hidden based on cradle requirements
                            if (argsContainer) argsContainer.style.display = selectedCradle?.uses_args ? 'block' : 'none';
                        } else {
                            // Hide all extra fields if no cradle selected
                            cradleObfContainer.style.display = 'none';
                            if (manualOverrideContainer) manualOverrideContainer.style.display = 'none';
                            if (autoDetectedContainer) autoDetectedContainer.style.display = 'none';
                            if (namespaceContainer) namespaceContainer.style.display = 'none';
                            if (classContainer) classContainer.style.display = 'none';
                            if (entryPointContainer) entryPointContainer.style.display = 'none';
                            if (argsContainer) argsContainer.style.display = 'none';
                        }
                        
                        // Revalidate when visibility changes
                        validateAllParameters();
                    };
                    
                    cradleCheckbox.addEventListener('change', updateCradleVisibility);
                    if (cradleMethodSelect) {
                        cradleMethodSelect.addEventListener('change', updateCradleVisibility);
                    }
                    
                    // Manual override checkbox listener
                    if (manualOverrideCheckbox) {
                        manualOverrideCheckbox.addEventListener('change', updateCradleVisibility);
                    }
                    
                    // C# obfuscation checkbox listener (to disable manual override when enabled)
                    const csObfCheckbox = document.getElementById('obfuscate-cs-names');
                    if (csObfCheckbox) {
                        csObfCheckbox.addEventListener('change', updateCradleVisibility);
                    }
                    
                    updateCradleVisibility();
                    
                    // Add validation listeners for cradle fields
                    const csCradleLhostInput = document.getElementById('cs-cradle-lhost');
                    const csCradleLportInput = document.getElementById('cs-cradle-lport');
                    if (csCradleLhostInput) {
                        csCradleLhostInput.addEventListener('input', () => {
                            validateAllParameters();
                        });
                        csCradleLhostInput.addEventListener('blur', () => {
                            validateAllParameters();
                        });
                    }
                    if (csCradleLportInput) {
                        csCradleLportInput.addEventListener('input', () => {
                            validateAllParameters();
                        });
                        csCradleLportInput.addEventListener('blur', () => {
                            validateAllParameters();
                        });
                    }
                }
            }, 0);
        }
    }
    
    // Add build options section
    html += `
        <div class="param-form-separator"></div>
        <div class="param-form-section-title">Build Options</div>
    `;
    
    // Only show "remove comments" option for template-based recipes
    // outputType already declared above
    if (outputType === 'template') {
        html += `
            <div class="param-form-item">
                <label class="param-form-checkbox-label">
                    <input type="checkbox" id="build-remove-comments" class="param-form-checkbox" checked>
                    Remove comments from source code
                </label>
                <div class="param-form-description">Strip comments and empty lines before compilation</div>
            </div>
            <div class="param-form-item">
                <label class="param-form-checkbox-label">
                    <input type="checkbox" id="build-remove-console" class="param-form-checkbox" checked>
                    Remove console output
                </label>
                <div class="param-form-description">Remove console output statements (e.g., Console.WriteLine, printf)</div>
            </div>
        `;
    }
    
    html += `
        <div class="param-form-item">
            <label class="param-form-checkbox-label">
                <input type="checkbox" id="build-strip-binaries" class="param-form-checkbox">
                Strip binary metadata
            </label>
            <div class="param-form-description">Remove debug symbols and metadata from compiled binaries.<br>Warning: On PE files it will however mark metadata with e.g. "No debug"</div>
        </div>
        <div class="param-form-item">
            <label class="param-form-checkbox-label">
                <input type="checkbox" id="amsi-bypass-launch" class="param-form-checkbox">
                Insert AMSI bypass in launch instructions
            </label>
            <div class="param-form-description">Inject AMSI bypass into PowerShell code blocks</div>
        </div>
        <div class="param-form-item" id="amsi-bypass-launch-method-container" style="display: none;">
            <label class="param-form-label">
                Bypass Method
                <span class="param-type">[choice]</span>
            </label>
            <select class="param-form-select" id="amsi-bypass-launch-method">
                ${amsiBypasses.map(bypass => `<option value="${bypass.name}">${bypass.name}</option>`).join('')}
            </select>
            <div class="param-form-description">AMSI bypass method</div>
        </div>
        <div class="param-form-item" id="amsi-bypass-launch-obf-container" style="display: none;">
            <label class="param-form-label">
                Obfuscate AMSI Bypass
                <span class="param-type">[choice]</span>
            </label>
            <select class="param-form-select" id="amsi-bypass-launch-obf-method">
                <option value="">None</option>
                ${psObfMethods.map(method => `<option value="${method.name}">${method.name}</option>`).join('')}
            </select>
            <div class="param-form-description">Obfuscation to apply to AMSI bypass in launch instructions</div>
        </div>
        <div class="param-form-item">
            <label class="param-form-checkbox-label">
                <input type="checkbox" id="obfuscate-launch-ps" class="param-form-checkbox">
                Obfuscate PowerShell in launch instructions
            </label>
            <div class="param-form-description">Apply obfuscation to PowerShell code blocks in launch instructions</div>
        </div>
        <div class="param-form-item" id="obfuscate-launch-ps-level-container" style="display: none;">
            <label class="param-form-label">
                Obfuscation Method
                <span class="param-type">[choice]</span>
            </label>
            <select class="param-form-select" id="obfuscate-launch-ps-level">
                ${psObfMethods.map((method, idx) => `<option value="${method.name}" ${idx === 2 ? 'selected' : ''}>${method.name}</option>`).join('')}
            </select>
            <div class="param-form-description">Obfuscation method to apply to PowerShell in launch instructions</div>
        </div>
    `;
    
    // Add event listeners for launch instructions options
    setTimeout(() => {
        const amsiLaunchCheckbox = document.getElementById('amsi-bypass-launch');
        const amsiLaunchContainer = document.getElementById('amsi-bypass-launch-method-container');
        const amsiLaunchObfContainer = document.getElementById('amsi-bypass-launch-obf-container');
        const amsiLaunchMethodSelect = document.getElementById('amsi-bypass-launch-method');
        
        const obfCheckbox = document.getElementById('obfuscate-launch-ps');
        const levelContainer = document.getElementById('obfuscate-launch-ps-level-container');
        
        if (amsiLaunchCheckbox && amsiLaunchContainer) {
            const updateAmsiVisibility = () => {
                const checked = amsiLaunchCheckbox.checked;
                amsiLaunchContainer.style.display = checked ? 'block' : 'none';
                
                // Show obfuscation option if AMSI is enabled and method allows obfuscation
                if (checked && amsiLaunchMethodSelect) {
                    const selectedMethod = amsiBypasses.find(b => b.name === amsiLaunchMethodSelect.value);
                    amsiLaunchObfContainer.style.display = (selectedMethod && !selectedMethod.no_obf) ? 'block' : 'none';
                } else {
                    amsiLaunchObfContainer.style.display = 'none';
                }
            };
            
            amsiLaunchCheckbox.addEventListener('change', updateAmsiVisibility);
            if (amsiLaunchMethodSelect) {
                amsiLaunchMethodSelect.addEventListener('change', updateAmsiVisibility);
            }
            updateAmsiVisibility();
        }
        
        if (obfCheckbox && levelContainer) {
            const updateLevelVisibility = () => {
                levelContainer.style.display = obfCheckbox.checked ? 'block' : 'none';
            };
            
            obfCheckbox.addEventListener('change', updateLevelVisibility);
            updateLevelVisibility();
        }
    }, 0);
    
    container.innerHTML = html;
    
    // Add event listeners for shellcode selection changes
    const shellcodeSelects = document.querySelectorAll('.shellcode-selection');
    shellcodeSelects.forEach((select, idx) => {
        select.addEventListener('change', async function() {
            await loadShellcodeParameters(this.value, idx);
        });
        
        // Load initial parameters for the first (default) selection
        if (select.selectedIndex > 0) {
            const selectedValue = select.options[select.selectedIndex].value;
            if (selectedValue) {
                loadShellcodeParameters(selectedValue, idx);
            }
        }
    });
    
    // Add event listeners for preprocessing option changes
    const preprocessingSelects = document.querySelectorAll('.preprocessing-option');
    preprocessingSelects.forEach((select, idx) => {
        select.addEventListener('change', function() {
            updateConditionalParameters();
        });
    });
    
    // Add event listeners for validation
    const inputs = document.querySelectorAll('.param-form-input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            validateParameter(input);
            validateAllParameters();
        });
        input.addEventListener('blur', () => {
            validateParameter(input);
            validateAllParameters();
        });
    });
    
    // Initial update of conditional parameters visibility
    updateConditionalParameters();
    
    // Initial validation of all fields
    validateAllParameters();
    
    document.getElementById('param-modal').classList.add('active');
}

// Update visibility of conditional parameters based on preprocessing option selection
function updateConditionalParameters() {
    if (!selectedRecipe) return;
    
    // Get all selected preprocessing options
    const selectedOptions = new Set();
    const preprocessingOptions = selectedRecipe.preprocessing?.filter(p => p.type === 'option') || [];
    
    preprocessingOptions.forEach((optionStep, idx) => {
        const selectElement = document.getElementById(`preprocessing-option-${idx}`);
        if (selectElement) {
            const selectedIndex = parseInt(selectElement.value);
            const options = optionStep.options || [];
            if (selectedIndex >= 0 && selectedIndex < options.length) {
                const selectedOption = options[selectedIndex];
                selectedOptions.add(selectedOption.name);
            }
        }
    });
    
    // Show/hide conditional parameters based on selected options
    const conditionalParams = document.querySelectorAll('.param-conditional');
    conditionalParams.forEach(paramDiv => {
        const requiredFor = paramDiv.getAttribute('data-required-for');
        if (requiredFor && selectedOptions.has(requiredFor)) {
            paramDiv.style.display = 'block';
        } else if (requiredFor) {
            paramDiv.style.display = 'none';
        }
    });
}

// Load shellcode-specific parameters dynamically
async function loadShellcodeParameters(shellcodeName, shellcodeIdx) {
    if (!shellcodeName) {
        // Clear parameters if no shellcode selected
        const container = document.getElementById(`shellcode-params-${shellcodeIdx}`);
        if (container) {
            container.innerHTML = '';
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/shellcode/${encodeURIComponent(shellcodeName)}`);
        const shellcode = await response.json();
        
        if (shellcode.error) {
            console.error('Failed to load shellcode:', shellcode.error);
            return;
        }
        
        const container = document.getElementById(`shellcode-params-${shellcodeIdx}`);
        if (!container) return;
        
        let html = '';
        
        if (shellcode.parameters && shellcode.parameters.length > 0) {
            shellcode.parameters.forEach(param => {
                const isRequired = param.required || false;
                const paramName = `shellcode_${shellcodeIdx}_${param.name}`;
                
                html += `
                    <div class="param-form-item">
                        <label class="param-form-label">
                            ${param.name}
                            ${isRequired ? '<span class="param-required">*</span>' : ''}
                            <span class="param-type">[${param.type}]</span>
                        </label>
                `;
                
                if (param.type === 'choice' && param.choices) {
                    html += `
                        <select class="param-form-select" data-param="${paramName}">
                            <option value="">-- Select --</option>
                            ${param.choices.map(c => `
                                <option value="${c}" ${param.default === c ? 'selected' : ''}>${c}</option>
                            `).join('')}
                        </select>
                    `;
                } else if (param.type === 'option' && param.options) {
                    html += `
                        <select class="param-form-select" data-param="${paramName}">
                            <option value="">-- Select --</option>
                            ${param.options.map(c => `
                                <option value="${c}" ${param.default === c ? 'selected' : ''}>${c}</option>
                            `).join('')}
                        </select>
                    `;
                } else if (param.type === 'bool') {
                    html += `
                        <select class="param-form-select" data-param="${paramName}">
                            <option value="true" ${param.default === true ? 'selected' : ''}>True</option>
                            <option value="false" ${param.default === false ? 'selected' : ''}>False</option>
                        </select>
                    `;
                } else {
                    // Process default value with template substitution
                    let defaultVal = param.default !== undefined ? param.default : '';
                    defaultVal = processParameterDefault(defaultVal, param.name);
                    
                    // Check if this is an lhost parameter and use default from settings
                    if (param.name.toLowerCase() === 'lhost') {
                        const settingsLhost = getDefaultLhost();
                        if (settingsLhost) {
                            defaultVal = settingsLhost;
                        }
                    }
                    
                    html += `
                        <input type="text" 
                               class="param-form-input" 
                               data-param="${paramName}"
                               data-type="${param.type}"
                               data-required="${isRequired}"
                               value="${escapeHtml(String(defaultVal))}"
                               placeholder="${param.description || ''}">
                        <div class="param-form-error" id="error-${paramName}"></div>
                    `;
                }
                
                html += `
                        <div class="param-form-description">${escapeHtml(param.description || '')}</div>
                    </div>
                `;
            });
        }
        
        container.innerHTML = html;
        
        // Add event listeners for validation on the new inputs
        const inputs = container.querySelectorAll('.param-form-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                validateParameter(input);
                validateAllParameters();
            });
            input.addEventListener('blur', () => {
                validateParameter(input);
                validateAllParameters();
            });
        });
        
        // Revalidate all parameters
        validateAllParameters();
    } catch (error) {
        console.error('Failed to load shellcode parameters:', error);
    }
}

// Update visibility of conditional parameters based on preprocessing option selection (OLD FUNCTION)
function updateConditionalParameters() {
    if (!selectedRecipe) return;
    
    // Get all selected preprocessing options
    const selectedOptions = {};
    const preprocessingOptions = selectedRecipe.preprocessing?.filter(p => p.type === 'option') || [];
    
    preprocessingOptions.forEach((optionStep, idx) => {
        const selectElement = document.getElementById(`preprocessing-option-${idx}`);
        if (selectElement) {
            const selectedIndex = parseInt(selectElement.value);
            const selectedOption = optionStep.options[selectedIndex];
            if (selectedOption) {
                selectedOptions[optionStep.name] = selectedOption.name;
            }
        }
    });
    
    // Show/hide conditional parameters
    const conditionalParams = document.querySelectorAll('.param-conditional');
    conditionalParams.forEach(paramElement => {
        const requiredFor = paramElement.getAttribute('data-required-for');
        if (requiredFor) {
            // Check if any selected option matches this parameter's required-for value
            const shouldShow = Object.values(selectedOptions).includes(requiredFor);
            paramElement.style.display = shouldShow ? 'block' : 'none';
            
            // If showing, restore default value if input is empty
            if (shouldShow) {
                const input = paramElement.querySelector('.param-form-input, .param-form-select');
                if (input && !input.value) {
                    const paramName = input.getAttribute('data-param');
                    const param = selectedRecipe.parameters.find(p => p.name === paramName);
                    if (param && param.default !== undefined) {
                        input.value = param.default;
                    }
                }
            } else {
                // If hiding, clear value
                const input = paramElement.querySelector('.param-form-input, .param-form-select');
                if (input) {
                    input.value = '';
                }
            }
        }
    });
    
    // Revalidate all parameters
    validateAllParameters();
}

// Validate a single parameter
function validateParameter(input) {
    const paramName = input.dataset.param;
    const value = input.value.trim();
    const errorElement = document.getElementById(`error-${paramName}`);
    
    // For shellcode parameters, validate based on data-type and data-required attributes
    const paramType = input.dataset.type;
    const isRequired = input.dataset.required === 'true';
    
    // Find parameter definition from recipe (for regular parameters)
    let param = selectedRecipe.parameters?.find(p => p.name === paramName);
    
    // If not found in recipe params, it might be a shellcode param - use data attributes
    if (!param && paramType) {
        param = {
            type: paramType,
            required: isRequired,
            name: paramName
        };
    }
    
    if (!param) return true;
    
    let error = null;
    
    // Check required
    if (param.required && !value) {
        error = 'This field is required';
    }
    // Validate by type
    else if (value) {
        if (param.type === 'ip') {
            const ipPattern = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            if (!ipPattern.test(value)) {
                error = 'Invalid IP address format';
            }
        } else if (param.type === 'port') {
            const port = parseInt(value);
            if (isNaN(port) || port < 1 || port > 65535) {
                error = 'Port must be between 1 and 65535';
            }
        } else if (param.type === 'integer') {
            const num = parseInt(value);
            if (isNaN(num)) {
                error = 'Must be a valid integer';
            } else {
                if (param.min !== undefined && num < param.min) {
                    error = `Must be at least ${param.min}`;
                }
                if (param.max !== undefined && num > param.max) {
                    error = `Must be at most ${param.max}`;
                }
            }
        } else if (param.type === 'hex') {
            if (!/^[0-9a-fA-F]+$/.test(value)) {
                error = 'Must be valid hexadecimal (0-9, a-f)';
            }
        } else if (param.type === 'path') {
            if (value.includes('\\\\') || value.includes('//')) {
                error = 'Invalid path format';
            }
        }
    }
    
    // Update error display
    if (error) {
        errorElement.textContent = `⚠ ${error}`;
        input.classList.add('param-form-input-error');
        return false;
    } else {
        errorElement.textContent = '';
        input.classList.remove('param-form-input-error');
        return true;
    }
}

// Validate all parameters and update generate button state
function validateAllParameters() {
    const inputs = document.querySelectorAll('.param-form-input');
    let allValid = true;
    
    inputs.forEach(input => {
        // Skip validation for hidden parameters
        const paramContainer = input.closest('.param-conditional');
        if (paramContainer && paramContainer.style.display === 'none') {
            return; // Skip hidden parameters
        }
        
        if (!validateParameter(input)) {
            allValid = false;
        }
    });
    
    // Validate cradle fields if they're visible
    const psCradleCheckbox = document.getElementById('ps-cradle');
    if (psCradleCheckbox && psCradleCheckbox.checked) {
        const psCradleLhost = document.getElementById('ps-cradle-lhost');
        const lhostError = document.getElementById('error-ps-cradle-lhost');
        if (psCradleLhost && psCradleLhost.offsetParent !== null) { // Check if visible
            if (!psCradleLhost.value.trim()) {
                if (lhostError) {
                    lhostError.textContent = '⚠ This field is required';
                    psCradleLhost.classList.add('param-form-input-error');
                }
                allValid = false;
            } else if (lhostError) {
                lhostError.textContent = '';
                psCradleLhost.classList.remove('param-form-input-error');
            }
        }
    }
    
    const csCradleCheckbox = document.getElementById('cs-cradle');
    if (csCradleCheckbox && csCradleCheckbox.checked) {
        const csCradleLhost = document.getElementById('cs-cradle-lhost');
        const lhostError = document.getElementById('error-cs-cradle-lhost');
        if (csCradleLhost && csCradleLhost.offsetParent !== null) { // Check if visible
            if (!csCradleLhost.value.trim()) {
                if (lhostError) {
                    lhostError.textContent = '⚠ This field is required';
                    csCradleLhost.classList.add('param-form-input-error');
                }
                allValid = false;
            } else if (lhostError) {
                lhostError.textContent = '';
                csCradleLhost.classList.remove('param-form-input-error');
            }
        }
    }
    
    // Update button state
    const generateBtn = document.getElementById('confirm-generate-btn');
    if (generateBtn) {
        generateBtn.disabled = !allValid;
        if (allValid) {
            generateBtn.classList.remove('btn-disabled');
        } else {
            generateBtn.classList.add('btn-disabled');
        }
    }
    
    return allValid;
}

// Generate payload
async function generatePayload() {
    if (!selectedRecipe) return;
    
    // Validate all parameters before generating
    if (!validateAllParameters()) {
        return;
    }
    
    // Collect parameters
    const parameters = {};
    const inputs = document.querySelectorAll('.param-form-input, .param-form-select');
    
    // Clear previous errors
    document.querySelectorAll('.param-form-error').forEach(el => el.textContent = '');
    
    inputs.forEach(input => {
        const paramName = input.dataset.param;
        if (!paramName) return; // Skip non-parameter inputs
        
        // Skip hidden parameters
        const paramContainer = input.closest('.param-conditional');
        if (paramContainer && paramContainer.style.display === 'none') {
            return;
        }
        
        let value = input.value.trim();
        
        // Convert boolean strings
        if (value === 'true') value = true;
        if (value === 'false') value = false;
        
        // Convert numbers
        const param = selectedRecipe.parameters.find(p => p.name === paramName);
        if (param && param.type === 'integer' && value) {
            value = parseInt(value);
        } else if (param && param.type === 'port' && value) {
            value = parseInt(value);
        }
        
        if (value !== '') {
            parameters[paramName] = value;
        }
    });
    
    // Collect preprocessing option selections
    const preprocessingSelections = {};
    const preprocessingOptions = selectedRecipe.preprocessing?.filter(p => p.type === 'option') || [];
    preprocessingOptions.forEach((optionStep, idx) => {
        const selectElement = document.getElementById(`preprocessing-option-${idx}`);
        if (selectElement) {
            const selectedIndex = parseInt(selectElement.value);
            preprocessingSelections[optionStep.name] = selectedIndex;
        }
    });
    
    // Collect shellcode selections and parameters
    const shellcodeSteps = selectedRecipe.preprocessing?.filter(p => p.type === 'shellcode') || [];
    shellcodeSteps.forEach((shellcodeStep, idx) => {
        const outputVar = shellcodeStep.output_var || 'raw_shellcode';
        const selectElement = document.getElementById(`shellcode-select-${idx}`);
        
        if (selectElement && selectElement.value) {
            // Store the selected shellcode name
            const selectionKey = `${outputVar}_shellcode_selection`;
            preprocessingSelections[selectionKey] = selectElement.value;
            
            // Collect shellcode-specific parameters
            const shellcodeParamsContainer = document.getElementById(`shellcode-params-${idx}`);
            if (shellcodeParamsContainer) {
                const shellcodeInputs = shellcodeParamsContainer.querySelectorAll('.param-form-input, .param-form-select');
                shellcodeInputs.forEach(input => {
                    const paramName = input.dataset.param;
                    if (paramName && paramName.startsWith(`shellcode_${idx}_`)) {
                        // Extract the actual parameter name (remove prefix)
                        const actualParamName = paramName.substring(`shellcode_${idx}_`.length);
                        let value = input.value.trim();
                        
                        // Convert types
                        const paramType = input.dataset.type;
                        if (value === 'true') value = true;
                        if (value === 'false') value = false;
                        if (paramType === 'integer' && value) value = parseInt(value);
                        if (paramType === 'port' && value) value = parseInt(value);
                        
                        if (value !== '') {
                            parameters[actualParamName] = value;
                        }
                    }
                });
            }
        }
    });
    
    // Store parameters globally for launch instruction substitution
    window.currentBuildParameters = parameters;
    
    // Collect build options
    const buildOptions = {
        remove_comments: document.getElementById('build-remove-comments')?.checked || false,
        remove_console_output: document.getElementById('build-remove-console')?.checked || false,
        strip_binaries: document.getElementById('build-strip-binaries')?.checked || false
    };
    
    // Collect PowerShell obfuscation options
    const psObfuscateCheckbox = document.getElementById('ps-obfuscate');
    if (psObfuscateCheckbox) {
        buildOptions.ps_obfuscate = psObfuscateCheckbox.checked;
        if (psObfuscateCheckbox.checked) {
            const psObfuscateLevel = document.getElementById('ps-obfuscate-level');
            buildOptions.ps_obfuscate_level = psObfuscateLevel ? psObfuscateLevel.value : '';
        }
    }
    
    // Collect PowerShell AMSI bypass options for templates
    const psAmsiCheckbox = document.getElementById('ps-amsi-bypass');
    if (psAmsiCheckbox) {
        buildOptions.ps_amsi_bypass = psAmsiCheckbox.checked;
        if (psAmsiCheckbox.checked) {
            const psAmsiMethod = document.getElementById('ps-amsi-method');
            const psAmsiObfMethod = document.getElementById('ps-amsi-obf-method');
            buildOptions.ps_amsi_method = psAmsiMethod ? psAmsiMethod.value : '';
            buildOptions.ps_amsi_obf_method = psAmsiObfMethod ? psAmsiObfMethod.value : '';
        }
    }
    
    // Collect PowerShell cradle options
    const psCradleCheckbox = document.getElementById('ps-cradle');
    if (psCradleCheckbox) {
        buildOptions.ps_cradle = psCradleCheckbox.checked;
        if (psCradleCheckbox.checked) {
            const psCradleMethod = document.getElementById('ps-cradle-method');
            const psCradleObfMethod = document.getElementById('ps-cradle-obf-method');
            const psCradleLhost = document.getElementById('ps-cradle-lhost');
            const psCradleLport = document.getElementById('ps-cradle-lport');
            const lhostError = document.getElementById('error-ps-cradle-lhost');
            
            // Validate required cradle fields
            if (!psCradleLhost || !psCradleLhost.value.trim()) {
                if (lhostError) {
                    lhostError.textContent = '⚠ This field is required';
                    psCradleLhost.classList.add('param-form-input-error');
                    // Scroll to the error
                    psCradleLhost.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    psCradleLhost.focus();
                }
                showNotificationPopup('Please fill in all required cradle fields', 'error');
                return;
            } else if (lhostError) {
                lhostError.textContent = '';
                psCradleLhost.classList.remove('param-form-input-error');
            }
            
            buildOptions.ps_cradle_method = psCradleMethod ? psCradleMethod.value : '';
            buildOptions.ps_cradle_obf_method = psCradleObfMethod ? psCradleObfMethod.value : '';
            buildOptions.cradle_lhost = psCradleLhost.value.trim();
            buildOptions.cradle_lport = psCradleLport ? parseInt(psCradleLport.value) || 80 : 80;
            
            // Check manual override state
            const psCradleManualOverride = document.getElementById('ps-cradle-manual-override');
            buildOptions.cradle_manual_override = psCradleManualOverride ? psCradleManualOverride.checked : false;
            
            // Collect optional assembly loading fields (only if manual override is enabled)
            if (buildOptions.cradle_manual_override) {
                const psCradleNamespace = document.getElementById('ps-cradle-namespace');
                const psCradleClass = document.getElementById('ps-cradle-class');
                const psCradleEntryPoint = document.getElementById('ps-cradle-entry-point');
                
                if (psCradleNamespace && psCradleNamespace.offsetParent !== null) {
                    buildOptions.cradle_namespace = psCradleNamespace.value.trim();
                }
                if (psCradleClass && psCradleClass.offsetParent !== null) {
                    buildOptions.cradle_class = psCradleClass.value.trim();
                }
                if (psCradleEntryPoint && psCradleEntryPoint.offsetParent !== null) {
                    buildOptions.cradle_entry_point = psCradleEntryPoint.value.trim();
                }
            }
            
            // Collect args field (always collected if visible)
            const psCradleArgs = document.getElementById('ps-cradle-args');
            if (psCradleArgs && psCradleArgs.offsetParent !== null) {
                buildOptions.cradle_args = psCradleArgs.value.trim();
            }
        }
    }
    
    // Collect C# obfuscation options
    const csObfuscateNamesCheckbox = document.getElementById('cs-obfuscate-names');
    if (csObfuscateNamesCheckbox) {
        buildOptions.cs_obfuscate_names = csObfuscateNamesCheckbox.checked;
    }
    
    // Collect C# cradle options
    const csCradleCheckbox = document.getElementById('cs-cradle');
    if (csCradleCheckbox) {
        buildOptions.cs_cradle = csCradleCheckbox.checked;
        if (csCradleCheckbox.checked) {
            const csCradleMethod = document.getElementById('cs-cradle-method');
            const csCradleObfMethod = document.getElementById('cs-cradle-obf-method');
            const csCradleLhost = document.getElementById('cs-cradle-lhost');
            const csCradleLport = document.getElementById('cs-cradle-lport');
            const lhostError = document.getElementById('error-cs-cradle-lhost');
            
            // Validate required cradle fields (if not already set by PS cradle)
            if (!buildOptions.cradle_lhost) {
                if (!csCradleLhost || !csCradleLhost.value.trim()) {
                    if (lhostError) {
                        lhostError.textContent = '⚠ This field is required';
                        csCradleLhost.classList.add('param-form-input-error');
                        // Scroll to the error
                        csCradleLhost.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        csCradleLhost.focus();
                    }
                    showNotificationPopup('Please fill in all required cradle fields', 'error');
                    return;
                } else if (lhostError) {
                    lhostError.textContent = '';
                    csCradleLhost.classList.remove('param-form-input-error');
                }
                buildOptions.cradle_lhost = csCradleLhost.value.trim();
                buildOptions.cradle_lport = csCradleLport ? parseInt(csCradleLport.value) || 80 : 80;
            }
            
            buildOptions.cs_cradle_method = csCradleMethod ? csCradleMethod.value : '';
            buildOptions.cs_cradle_obf_method = csCradleObfMethod ? csCradleObfMethod.value : '';
            // Only set lhost/lport if not already set by PS cradle
            if (!buildOptions.cradle_lhost) {
                buildOptions.cradle_lhost = csCradleLhost ? csCradleLhost.value : '';
                buildOptions.cradle_lport = csCradleLport ? parseInt(csCradleLport.value) || 80 : 80;
            }
            
            // Check manual override state if not already set by PS cradle
            if (buildOptions.cradle_manual_override === undefined) {
                const csCradleManualOverride = document.getElementById('cs-cradle-manual-override');
                buildOptions.cradle_manual_override = csCradleManualOverride ? csCradleManualOverride.checked : false;
            }
            
            // Collect optional assembly loading fields (if not already set by PS cradle and manual override is enabled)
            if (!buildOptions.cradle_namespace && buildOptions.cradle_manual_override) {
                const csCradleNamespace = document.getElementById('cs-cradle-namespace');
                const csCradleClass = document.getElementById('cs-cradle-class');
                const csCradleEntryPoint = document.getElementById('cs-cradle-entry-point');
                
                if (csCradleNamespace && csCradleNamespace.offsetParent !== null) {
                    buildOptions.cradle_namespace = csCradleNamespace.value.trim();
                }
                if (csCradleClass && csCradleClass.offsetParent !== null) {
                    buildOptions.cradle_class = csCradleClass.value.trim();
                }
                if (csCradleEntryPoint && csCradleEntryPoint.offsetParent !== null) {
                    buildOptions.cradle_entry_point = csCradleEntryPoint.value.trim();
                }
            }
            
            // Collect args field (only if not already set by PS cradle)
            if (!buildOptions.cradle_args) {
                const csCradleArgs = document.getElementById('cs-cradle-args');
                if (csCradleArgs && csCradleArgs.offsetParent !== null) {
                    buildOptions.cradle_args = csCradleArgs.value.trim();
                }
            }
        }
    }
    
    // Collect AMSI bypass options for launch instructions
    const amsiLaunchCheckbox = document.getElementById('amsi-bypass-launch');
    if (amsiLaunchCheckbox) {
        buildOptions.amsi_bypass_launch = amsiLaunchCheckbox.checked;
        if (amsiLaunchCheckbox.checked) {
            const amsiLaunchMethod = document.getElementById('amsi-bypass-launch-method');
            const amsiLaunchObfMethod = document.getElementById('amsi-bypass-launch-obf-method');
            buildOptions.amsi_bypass_launch_method = amsiLaunchMethod ? amsiLaunchMethod.value : '';
            buildOptions.amsi_bypass_launch_obf_method = amsiLaunchObfMethod ? amsiLaunchObfMethod.value : '';
        }
    }
    
    // Collect launch instructions obfuscation options
    const launchPsObfuscateCheckbox = document.getElementById('obfuscate-launch-ps');
    if (launchPsObfuscateCheckbox) {
        buildOptions.obfuscate_launch_ps = launchPsObfuscateCheckbox.checked;
        if (launchPsObfuscateCheckbox.checked) {
            const launchPsObfuscateLevel = document.getElementById('obfuscate-launch-ps-level');
            buildOptions.obfuscate_launch_ps_level = launchPsObfuscateLevel ? launchPsObfuscateLevel.value : '';
        }
    }
    
    // Close parameter modal
    document.getElementById('param-modal').classList.remove('active');
    
    // Show build modal
    const buildModal = document.getElementById('build-modal');
    const stepsContainer = document.getElementById('build-steps-container');
    const resultContainer = document.getElementById('build-result');
    const closeBtn = document.getElementById('close-build-btn');
    
    stepsContainer.innerHTML = '';
    resultContainer.innerHTML = '';
    closeBtn.style.display = 'none';
    buildModal.classList.add('active');
    
    try {
        // Start build
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: selectedRecipe.category,
                recipe: selectedRecipe.name,
                parameters: parameters,
                preprocessing_selections: preprocessingSelections,
                build_options: buildOptions,
                version: selectedVersion
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Build failed');
        }
        
        // Poll for build status
        pollBuildStatus(data.session_id);
        
    } catch (error) {
        console.error('Build error:', error);
        stepsContainer.innerHTML = '';
        resultContainer.innerHTML = `
            <div class="build-result build-failed">
                <strong>✗ Build Failed</strong><br>
                ${error.message}
            </div>
        `;
        closeBtn.style.display = 'block';
    }
}

// Poll build status
async function pollBuildStatus(sessionId) {
    const stepsContainer = document.getElementById('build-steps-container');
    const resultContainer = document.getElementById('build-result');
    const closeBtn = document.getElementById('close-build-btn');
    let modalContent = null;
    
    // Add title above the container
    const modalBody = stepsContainer.parentElement;
    if (!document.getElementById('build-steps-title')) {
        const titleDiv = document.createElement('div');
        titleDiv.id = 'build-steps-title';
        titleDiv.style.color = 'var(--mauve)';
        titleDiv.style.fontWeight = 'bold';
        titleDiv.style.marginBottom = '0.5rem';
        titleDiv.textContent = 'Building steps';
        modalBody.insertBefore(titleDiv, stepsContainer);
    }
    
    // Hourglass animation frames
    const spinnerFrames = ["⌛"];
    let spinnerIndex = 0;
    let isComplete = false;
    
    // Track steps by name to update in place
    const stepElements = new Map();
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/build-status/${sessionId}`);
            const data = await response.json();
            
            // Check if build is complete
            if (data.status === 'success' || data.status === 'failed') {
                isComplete = true;
            }
            
            // Update spinner only if not complete
            if (!isComplete) {
                spinnerIndex = (spinnerIndex + 1) % spinnerFrames.length;
            }
            
            // Render or update steps
            data.steps.forEach(step => {
                let statusIcon = '⏳';
                let statusColor = 'var(--overlay1)';
                
                if (step.status === 'running') {
                    statusIcon = '⌛';  // Hourglass
                    statusColor = 'var(--yellow)';
                } else if (step.status === 'success') {
                    statusIcon = '✅';
                    statusColor = 'var(--green)';
                } else if (step.status === 'failed') {
                    statusIcon = '❌';
                    statusColor = 'var(--red)';
                }
                
                // Check if step already exists
                if (stepElements.has(step.name)) {
                    // Update existing step
                    const stepDiv = stepElements.get(step.name);
                    const stepHeader = stepDiv.querySelector('.step-header');
                    stepHeader.innerHTML = `<span style="font-weight: bold;">${statusIcon} ${escapeHtml(step.name)}</span>`;
                    stepHeader.style.color = statusColor;
                    
                    // Update debug output if enabled and present
                    if (window.showBuildDebug) {
                        let debugDiv = stepDiv.querySelector('.step-debug');
                        if (!debugDiv && (step.output || step.error)) {
                            debugDiv = document.createElement('div');
                            debugDiv.className = 'step-debug';
                            debugDiv.style.marginLeft = '2rem';
                            debugDiv.style.fontSize = '0.85em';
                            debugDiv.style.marginTop = '0.25rem';
                            stepDiv.appendChild(debugDiv);
                        }
                        
                        if (debugDiv) {
                            let debugHtml = '';
                            if (step.output && step.output.trim()) {
                                // Truncate output to 500 chars
                                let output = step.output.trim();
                                if (output.length > 500) {
                                    output = output.substring(0, 500) + '... (truncated)';
                                }
                                const outputLines = output.split('\n').slice(0, 10);
                                debugHtml += outputLines.map(line => 
                                    `<div style="color: var(--subtext0);">${escapeHtml(line)}</div>`
                                ).join('');
                            }
                            if (step.error && step.error.trim()) {
                                let error = step.error.trim();
                                if (error.length > 500) {
                                    error = error.substring(0, 500) + '... (truncated)';
                                }
                                const errorLines = error.split('\n').slice(0, 10);
                                debugHtml += errorLines.map(line => 
                                    `<div style="color: var(--red);">Error: ${escapeHtml(line)}</div>`
                                ).join('');
                            }
                            debugDiv.innerHTML = debugHtml;
                        }
                    }
                } else {
                    // Create new step
                    const stepDiv = document.createElement('div');
                    stepDiv.className = 'build-step';
                    stepDiv.style.marginBottom = '0.5rem';
                    
                    const stepHeader = document.createElement('div');
                    stepHeader.className = 'step-header';
                    stepHeader.style.color = statusColor;
                    stepHeader.innerHTML = `<span style="font-weight: bold;">${statusIcon} ${escapeHtml(step.name)}</span>`;
                    stepDiv.appendChild(stepHeader);
                    
                    // Add debug output if enabled
                    if (window.showBuildDebug && (step.output || step.error)) {
                        const debugDiv = document.createElement('div');
                        debugDiv.className = 'step-debug';
                        debugDiv.style.marginLeft = '2rem';
                        debugDiv.style.fontSize = '0.85em';
                        debugDiv.style.marginTop = '0.25rem';
                        
                        let debugHtml = '';
                        if (step.output && step.output.trim()) {
                            // Truncate output to 500 chars
                            let output = step.output.trim();
                            if (output.length > 500) {
                                output = output.substring(0, 500) + '... (truncated)';
                            }
                            const outputLines = output.split('\n').slice(0, 10);
                            debugHtml += outputLines.map(line => 
                                `<div style="color: var(--subtext0);">${escapeHtml(line)}</div>`
                            ).join('');
                        }
                        if (step.error && step.error.trim()) {
                            let error = step.error.trim();
                            if (error.length > 500) {
                                error = error.substring(0, 500) + '... (truncated)';
                            }
                            const errorLines = error.split('\n').slice(0, 10);
                            debugHtml += errorLines.map(line => 
                                `<div style="color: var(--red);">Error: ${escapeHtml(line)}</div>`
                            ).join('');
                        }
                        debugDiv.innerHTML = debugHtml;
                        stepDiv.appendChild(debugDiv);
                    }
                    
                    stepsContainer.appendChild(stepDiv);
                    stepElements.set(step.name, stepDiv);
                }
            });
            
            // Auto-scroll to bottom
            stepsContainer.scrollTop = stepsContainer.scrollHeight;
            
            // Check if build is complete
            if (data.status === 'success') {
                clearInterval(interval);
                
                // Get file size if available
                let sizeInfo = '';
                if (data.output_file) {
                    // Size info would come from backend
                    sizeInfo = '';
                }
                
                resultContainer.innerHTML = `
                    <div style="background: var(--surface0); padding: 1rem; border-radius: 4px; border-left: 3px solid var(--green);">
                        <div style="color: var(--green); font-weight: bold; margin-bottom: 0.5rem;">✅ Build completed successfully!</div>
                        <div style="color: var(--text);">Output: ${escapeHtml(data.output_file)}${sizeInfo}</div>
                    </div>
                `;
                
                // Show launch instructions if available
                if (data.launch_instructions) {
                    // Substitute parameter values in launch instructions
                    let instructions = data.launch_instructions;
                    if (window.currentBuildParameters) {
                        Object.keys(window.currentBuildParameters).forEach(paramName => {
                            const paramValue = window.currentBuildParameters[paramName];
                            // Replace both {{ paramName }} and {{paramName}} patterns
                            const regex1 = new RegExp(`{{\\s*${paramName}\\s*}}`, 'g');
                            const regex2 = new RegExp(`{\\{\\s*${paramName}\\s*\\}}`, 'g');
                            instructions = instructions.replace(regex1, paramValue);
                            instructions = instructions.replace(regex2, paramValue);
                        });
                    }
                    
                    // Also substitute {{ global.lhost }} if present
                    if (instructions.includes('{{ global.lhost }}') || instructions.includes('{{global.lhost}}')) {
                        const globalLhost = getDefaultLhost() || '127.0.0.1';
                        instructions = instructions.replace(/\{\{\s*global\.lhost\s*\}\}/g, globalLhost);
                    }

                    // Substitute {{ global.output_dir }} if present
                    if (instructions.includes('{{ global.output_dir }}') || instructions.includes('{{global.output_dir}}')) {
                        const globalOutputDir = getDefaultOutputDir() || '/tmp/paygen-output';
                        instructions = instructions.replace(/\{\{\s*global\.output_dir\s*\}\}/g, globalOutputDir);
                    }
                    
                    resultContainer.innerHTML += `
                        <div style="margin-top: 1rem; background: var(--surface0); padding: 1rem; border-radius: 4px; border-left: 3px solid var(--blue);">
                            <div style="color: var(--blue); font-weight: bold; margin-bottom: 0.5rem;">Launch Instructions:</div>
                            <div class="launch-instructions-markdown" id="launch-instructions-md-build"></div>
                        </div>
                    `;
                    
                    // Render launch instructions using the same method as recipe details
                    renderLaunchInstructions(instructions, 'launch-instructions-md-build');
                }
                
                // Auto-scroll to show the complete message (with or without instructions)
                setTimeout(() => {
                    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    modalContent = document.querySelector('#build-progress-modal .modal-content');
                    if (modalContent) {
                        modalContent.scrollTop = modalContent.scrollHeight;
                    }
                }, 100);
                
                closeBtn.style.display = 'block';
            } else if (data.status === 'failed') {
                clearInterval(interval);
                resultContainer.innerHTML = `
                    <div style="background: var(--surface0); padding: 1rem; border-radius: 4px; border-left: 3px solid var(--red);">
                        <div style="color: var(--red); font-weight: bold;">❌ Build failed</div>
                        ${data.error ? `<div style="color: var(--text); margin-top: 0.5rem;">${escapeHtml(data.error)}</div>` : ''}
                    </div>
                `;
                
                // Auto-scroll to show the error message
                resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                modalContent = document.querySelector('#build-progress-modal .modal-content');
                if (modalContent) {
                    modalContent.scrollTop = modalContent.scrollHeight;
                }
                
                closeBtn.style.display = 'block';
            }
            
        } catch (error) {
            clearInterval(interval);
            console.error('Status poll error:', error);
            resultContainer.innerHTML = `
                <div class="build-result build-failed">
                    <strong>✗ Error</strong><br>
                    Failed to get build status
                </div>
            `;
            closeBtn.style.display = 'block';
        }
    }, 500); // Poll every 500ms
}

// Show history
async function showHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        // Update stats
        const stats = data.stats || {total: 0, success: 0, failed: 0, showing: 0};
        let statsText = `Total: ${stats.total} | Success: ${stats.success} | Failed: ${stats.failed}`;
        if (stats.showing < stats.total) {
            statsText += ` | Showing: ${stats.showing} recent`;
        }
        document.getElementById('history-stats').textContent = statsText;
        
        const container = document.getElementById('history-container');
        
        if (data.entries.length === 0) {
            container.innerHTML = `
                <div class="placeholder">
                    <p>No history entries yet.</p>
                    <p style="color: var(--subtext0); font-size: 0.9rem;">Generate a payload to see it here!</p>
                </div>
            `;
        } else {
            // Show summary list
            let html = '';
            data.entries.forEach((entry, index) => {
                const statusClass = entry.success ? 'success' : 'failed';
                const statusIcon = entry.success ? '✓' : '✗';
                
                html += `
                    <div class="history-summary ${statusClass}" onclick="showHistoryDetail(${index})">
                        <div class="history-summary-header">
                            <div class="history-summary-title">
                                <span class="history-status-icon ${statusClass}">${statusIcon}</span>
                                <span class="history-recipe">${escapeHtml(entry.recipe_name)}</span>
                            </div>
                            <span class="history-timestamp">${entry.formatted_timestamp}</span>
                        </div>
                        <div class="history-summary-output">
                            ${escapeHtml(entry.output_filename)}
                        </div>
                        <div class="history-summary-action">
                            Click to view details →
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        // Reset footer buttons to list mode
        const clearBtn = document.getElementById('clear-history-btn');
        const backBtn = document.getElementById('back-history-btn');
        const regenerateBtn = document.getElementById('regenerate-history-btn');
        const modifyBtn = document.getElementById('modify-regenerate-history-btn');
        if (clearBtn) {
            clearBtn.textContent = 'Clear All';
            clearBtn.onclick = clearHistory;
        }
        if (backBtn) {
            backBtn.style.display = 'none';
        }
        if (regenerateBtn) {
            regenerateBtn.style.display = 'none';
        }
        if (modifyBtn) {
            modifyBtn.style.display = 'none';
        }
        
        document.getElementById('history-modal').classList.add('active');
        
    } catch (error) {
        console.error('Failed to load history:', error);
        alert('Failed to load build history');
    }
}

// Show detailed view of a history entry
async function showHistoryDetail(index) {
    // Fetch full entry details
    try {
        const response = await fetch(`/api/history/${index}`);
        const entry = await response.json();
        
        if (entry.error) {
            alert('Failed to load entry details');
            return;
        }
        
        const container = document.getElementById('history-container');
        const statusClass = entry.success ? 'success' : 'failed';
        const statusIcon = entry.success ? '✓' : '✗';
    
    let html = `
        <div class="history-detail">
            <div class="history-detail-header">
                <div class="history-detail-title">
                    <span class="history-status-icon ${statusClass}">${statusIcon}</span>
                    <span class="history-recipe">${escapeHtml(entry.recipe_name)}</span>
                </div>
                <span class="history-timestamp">${entry.formatted_timestamp}</span>
            </div>
            
            <div class="history-detail-section">
                <div class="history-detail-section-title">Output File</div>
                <div class="history-detail-content">${escapeHtml(entry.output_file)}</div>
            </div>
    `;
    
    // Parameters section
    if (Object.keys(entry.parameters).length > 0) {
        html += `
            <div class="history-detail-section">
                <div class="history-detail-section-title">Parameters</div>
                <div class="history-detail-content">
                    ${Object.entries(entry.parameters).map(([k, v]) => 
                        `<div class="history-param-row">
                            <span class="history-param-key">${escapeHtml(k)}:</span>
                            <span class="history-param-value">${escapeHtml(String(v))}</span>
                        </div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    // Build options section (language-specific and build options)
    if (entry.build_options && Object.keys(entry.build_options).length > 0) {
        // Categorize build options
        const languageOptions = {};
        const buildOptions = {};
        
        // Define which options belong to each category
        const languageSpecificKeys = [
            'obfuscate_cs_names', 'cs_obfuscate_names', 'cs_obfuscation_names', // C# name obfuscation variations
            'cs_obfuscation_level',
            'obfuscate_ps', 'ps_obfuscate', 'ps_obfuscation', // PowerShell obfuscation variations
            'ps_obfuscate_level', 'ps_obfuscation_level',
            'amsi_bypass', 'ps_amsi_bypass', 'amsi_bypass_method', 'ps_amsi_method', 'ps_amsi_obf_method', // AMSI bypass variations
            'ps_cradle', 'ps_cradle_method', 'ps_cradle_obf_method',
            'cs_cradle', 'cs_cradle_method', 'cs_cradle_obf_method',
            'cradle_lhost', 'cradle_lport', 'cradle_manual_override',
            'cradle_namespace', 'cradle_class', 'cradle_entry_point', 'cradle_args'
        ];
        
        const buildOptionKeys = [
            'remove_comments', 'remove_console_output', 'strip_binaries',
            'amsi_bypass_launch', 'amsi_bypass_launch_method', 'amsi_bypass_launch_obf_method',
            'obfuscate_launch_ps', 'obfuscate_launch_ps_level'
        ];
        
        Object.entries(entry.build_options).forEach(([k, v]) => {
            if (languageSpecificKeys.includes(k)) {
                languageOptions[k] = v;
            } else if (buildOptionKeys.includes(k)) {
                buildOptions[k] = v;
            }
        });
        
        // Format option name for display (matching the UI text exactly)
        const formatOptionName = (key) => {
            const nameMap = {
                // C# Language Options (all variations)
                'obfuscate_cs_names': 'Obfuscate function/variable names',
                'cs_obfuscate_names': 'Obfuscate function/variable names',
                'cs_obfuscation_names': 'Obfuscate function/variable names',
                'cs_obfuscation_level': 'C# obfuscation level',
                'cs_cradle': 'Add download cradle',
                
                // PowerShell Language Options
                'amsi_bypass': 'Insert AMSI bypass',
                'ps_amsi_bypass': 'Insert AMSI bypass',
                'obfuscate_ps': 'Obfuscate PowerShell script',
                'ps_obfuscate': 'Obfuscate PowerShell script',
                'ps_obfuscation': 'Obfuscate PowerShell script',
                'ps_obfuscation_level': 'PowerShell obfuscation level',
                'ps_obfuscate_level': 'PowerShell obfuscation level',
                'ps_cradle': 'Add download cradle',
                
                // Build Options
                'remove_comments': 'Remove comments from source code',
                'remove_console_output': 'Remove console output',
                'strip_binaries': 'Strip binary metadata',
                'amsi_bypass_launch': 'Insert AMSI bypass in launch instructions',
                'obfuscate_launch_ps': 'Obfuscate PowerShell in launch instructions',
                
                // Cradle details (shown when relevant)
                'cradle_lhost': 'Cradle LHOST',
                'cradle_lport': 'Cradle LPORT',
                'ps_cradle_method': 'PowerShell cradle method',
                'cs_cradle_method': 'C# cradle method',
                'ps_cradle_obf_method': 'PowerShell cradle obfuscation',
                'cs_cradle_obf_method': 'C# cradle obfuscation',
                'amsi_bypass_method': 'AMSI bypass method',
                'ps_amsi_method': 'AMSI bypass method',
                'amsi_bypass_obf_method': 'AMSI bypass obfuscation',
                'ps_amsi_obf_method': 'AMSI bypass obfuscation',
                'amsi_bypass_launch_method': 'Launch AMSI bypass method',
                'amsi_bypass_launch_obf_method': 'Launch AMSI bypass obfuscation',
                'obfuscate_launch_ps_level': 'Launch PowerShell obfuscation level'
            };
            
            if (nameMap[key]) return nameMap[key];
            return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        };
        
        // Format option value for display
        const formatOptionValue = (value) => {
            if (typeof value === 'boolean') {
                return value ? '✓ Enabled' : '✗ Disabled';
            }
            return escapeHtml(String(value));
        };
        
        let optionsHtml = '';
        
        // Language-specific options
        if (Object.keys(languageOptions).length > 0) {
            optionsHtml += '<div style="margin-bottom: 1rem;"><strong style="color: var(--mauve);">Language Specific Options:</strong></div>';
            Object.entries(languageOptions).forEach(([k, v]) => {
                optionsHtml += `
                    <div class="history-param-row">
                        <span class="history-param-key">${escapeHtml(formatOptionName(k))}:</span>
                        <span class="history-param-value">${formatOptionValue(v)}</span>
                    </div>`;
            });
        }
        
        // Build options
        if (Object.keys(buildOptions).length > 0) {
            if (optionsHtml) optionsHtml += '<div style="margin: 1rem 0;"></div>';
            optionsHtml += '<div style="margin-bottom: 1rem;"><strong style="color: var(--mauve);">Build Options:</strong></div>';
            Object.entries(buildOptions).forEach(([k, v]) => {
                optionsHtml += `
                    <div class="history-param-row">
                        <span class="history-param-key">${escapeHtml(formatOptionName(k))}:</span>
                        <span class="history-param-value">${formatOptionValue(v)}</span>
                    </div>`;
            });
        }
        
        if (optionsHtml) {
            html += `
                <div class="history-detail-section">
                    <div class="history-detail-section-title">Build Options</div>
                    <div class="history-detail-content">
                        ${optionsHtml}
                    </div>
                </div>
            `;
        }
    }
    
    // Build steps section
    if (entry.build_steps && entry.build_steps.length > 0) {
        html += `
            <div class="history-detail-section">
                <div class="history-detail-section-title">Build Steps</div>
                <div class="history-detail-content">
                    ${entry.build_steps.map(step => {
                        const stepStatus = step.status || 'pending';
                        const stepIcon = {
                            'success': '✓',
                            'failed': '✗',
                            'running': '⏳',
                            'pending': '⏳'
                        }[stepStatus] || '?';
                        const stepColor = {
                            'success': 'var(--green)',
                            'failed': 'var(--red)',
                            'running': 'var(--yellow)',
                            'pending': 'var(--overlay1)'
                        }[stepStatus] || 'var(--text)';
                        return `
                            <div class="history-detail-step">
                                <span style="color: ${stepColor};">${stepIcon}</span>
                                ${escapeHtml(step.name)}
                                ${step.output ? `<div class="history-detail-step-output">${escapeHtml(step.output)}</div>` : ''}
                                ${step.error ? `<div class="history-detail-step-error">${escapeHtml(step.error)}</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    // Launch instructions section
    if (entry.launch_instructions) {
        html += `
            <div class="history-detail-section">
                <div class="history-detail-section-title">Launch Instructions</div>
                <div class="history-detail-content">
                    <div class="history-launch-content launch-instructions-markdown" id="history-launch-detail-${index}"></div>
                </div>
            </div>
        `;
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
    
    // Update footer buttons for detail mode
    const clearBtn = document.getElementById('clear-history-btn');
    const closeBtn = document.getElementById('close-history-btn');
    const backBtn = document.getElementById('back-history-btn');
    const regenerateBtn = document.getElementById('regenerate-history-btn');
    const modifyBtn = document.getElementById('modify-regenerate-history-btn');
    
    if (clearBtn) {
        clearBtn.textContent = 'Clear';
        clearBtn.onclick = () => deleteHistoryEntry(index);
    }
    if (backBtn) {
        backBtn.style.display = 'block';
        backBtn.onclick = () => {
            showHistory();
            // Reset buttons
            clearBtn.textContent = 'Clear All';
            clearBtn.onclick = clearHistory;
            backBtn.style.display = 'none';
            if (regenerateBtn) regenerateBtn.style.display = 'none';
            if (modifyBtn) modifyBtn.style.display = 'none';
        };
    }
    if (regenerateBtn) {
        regenerateBtn.style.display = 'block';
        regenerateBtn.onclick = () => regenerateFromHistory(index);
    }
    if (modifyBtn) {
        modifyBtn.style.display = 'block';
        modifyBtn.onclick = () => modifyAndRegenerateFromHistory(index);
    }
    
    // Render launch instructions if present
    if (entry.launch_instructions) {
        const launchContainer = document.getElementById(`history-launch-detail-${index}`);
        if (launchContainer) {
            // Substitute parameters in launch instructions
            let instructions = entry.launch_instructions;
            Object.entries(entry.parameters).forEach(([paramName, paramValue]) => {
                const regex1 = new RegExp(`{{\\s*${paramName}\\s*}}`, 'g');
                instructions = instructions.replace(regex1, paramValue);
            });
            
            // Render launch instructions with the correct container ID
            renderLaunchInstructions(instructions, `history-launch-detail-${index}`);
        }
    }
    } catch (error) {
        console.error('Failed to load history details:', error);
        alert('Failed to load entry details');
    }
}

// Delete single history entry
async function deleteHistoryEntry(index) {
    if (!confirm('Are you sure you want to delete this entry?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${index}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showHistory(); // Refresh history display
        } else {
            alert('Failed to delete entry');
        }
    } catch (error) {
        console.error('Failed to delete entry:', error);
        alert('Failed to delete entry');
    }
}

// Clear history
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all build history?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/history/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            showHistory(); // Refresh history display
        } else {
            alert('Failed to clear history');
        }
    } catch (error) {
        console.error('Failed to clear history:', error);
        alert('Failed to clear history');
    }
}

// Modify and regenerate from history (shows parameter form)
async function modifyAndRegenerateFromHistory(index) {
    try {
        const response = await fetch(`/api/history/${index}/regenerate`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (!data.success) {
            alert('Failed to load history entry');
            return;
        }
        
        // Close history modal
        document.getElementById('history-modal').classList.remove('active');
        
        // Find and select the recipe
        const recipeName = data.recipe_name;
        let found = false;
        
        for (const [category, categoryRecipes] of Object.entries(categories)) {
            const recipe = categoryRecipes.find(r => r.name === recipeName);
            if (recipe) {
                await selectRecipe(category, recipeName);
                found = true;
                break;
            }
        }
        
        if (!found) {
            alert(`Recipe '${recipeName}' not found. It may have been deleted.`);
            return;
        }
        
        // Wait for recipe to load
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Show parameter form
        showParameterForm();
        
        // Wait for parameter form to render
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Pre-fill regular parameters
        Object.entries(data.parameters).forEach(([paramName, paramValue]) => {
            const input = document.querySelector(`[name="${paramName}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = paramValue === true || paramValue === 'true';
                } else {
                    input.value = paramValue;
                }
            }
        });
        
        // Pre-fill preprocessing selections (shellcode dropdowns, etc.)
        if (data.preprocessing_selections) {
            for (const [selectionKey, selectionValue] of Object.entries(data.preprocessing_selections)) {
                // Check if this is a shellcode selection (format: {output_var}_shellcode_selection)
                if (selectionKey.endsWith('_shellcode_selection')) {
                    const outputVar = selectionKey.replace('_shellcode_selection', '');
                    // Find the shellcode select by data-output-var attribute
                    const selectElement = document.querySelector(`.shellcode-selection[data-output-var="${outputVar}"]`);
                    if (selectElement) {
                        // Set the value to the shellcode name
                        selectElement.value = selectionValue;
                        // Trigger change event to load dynamic parameters
                        selectElement.dispatchEvent(new Event('change'));
                        // Wait for parameters to load
                        await new Promise(resolve => setTimeout(resolve, 300));
                    }
                }
            }
        }
        
        // Pre-fill shellcode-specific parameters (like lhost, lport)
        // Need to wait a bit more for all parameters to fully load
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Shellcode parameters are stored without the shellcode prefix
        // We need to find all shellcode containers and fill their params
        Object.entries(data.parameters).forEach(([paramName, paramValue]) => {
            // Skip parameters that are already handled elsewhere
            if (paramName.startsWith('shellcode_')) return;
            
            // Try to find this parameter in all shellcode containers
            document.querySelectorAll('.shellcode-params-container').forEach(container => {
                // Extract shellcode index from container ID (shellcode-params-0 -> 0)
                const containerIdMatch = container.id.match(/shellcode-params-(\d+)/);
                if (containerIdMatch) {
                    const idx = containerIdMatch[1];
                    const fullParamName = `shellcode_${idx}_${paramName}`;
                    const input = container.querySelector(`[data-param="${fullParamName}"]`);
                    if (input) {
                        if (input.tagName === 'SELECT') {
                            input.value = paramValue;
                        } else if (input.type === 'checkbox') {
                            input.checked = paramValue === true || paramValue === 'true';
                        } else {
                            input.value = paramValue;
                        }
                    }
                }
            });
        });
        
        // Pre-fill build options
        if (data.build_options) {
            Object.entries(data.build_options).forEach(([optionKey, optionValue]) => {
                // Map option keys to checkbox IDs
                const checkboxId = optionKey.replace(/_/g, '-');
                const checkbox = document.getElementById(checkboxId);
                if (checkbox && checkbox.type === 'checkbox') {
                    checkbox.checked = optionValue === true;
                    // Trigger change event to show/hide dependent fields
                    checkbox.dispatchEvent(new Event('change'));
                }
                
                // Handle select dropdowns (like obfuscation levels)
                const selectId = optionKey.replace(/_/g, '-');
                const select = document.getElementById(selectId);
                if (select && select.tagName === 'SELECT') {
                    select.value = optionValue;
                }
            });
            
            // Wait for dynamic fields (like cradle inputs) to appear
            await new Promise(resolve => setTimeout(resolve, 400));
            
            // Second pass: fill in text inputs that appeared after checkboxes
            Object.entries(data.build_options).forEach(([optionKey, optionValue]) => {
                // Handle cradle parameters specially (shared between PS and CS)
                if (optionKey === 'cradle_lhost') {
                    // Fill both PS and CS cradle lhost fields
                    const psInput = document.getElementById('ps-cradle-lhost');
                    const csInput = document.getElementById('cs-cradle-lhost');
                    if (psInput && psInput.offsetParent !== null) {
                        psInput.value = optionValue;
                        // Clear any existing error state
                        psInput.classList.remove('param-form-input-error');
                        const psError = document.getElementById('error-ps-cradle-lhost');
                        if (psError) psError.textContent = '';
                        // Trigger input event to enable generate button
                        psInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    if (csInput && csInput.offsetParent !== null) {
                        csInput.value = optionValue;
                        // Clear any existing error state
                        csInput.classList.remove('param-form-input-error');
                        const csError = document.getElementById('error-cs-cradle-lhost');
                        if (csError) csError.textContent = '';
                        // Trigger input event to enable generate button
                        csInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                } else if (optionKey === 'cradle_lport') {
                    // Fill both PS and CS cradle lport fields
                    const psInput = document.getElementById('ps-cradle-lport');
                    const csInput = document.getElementById('cs-cradle-lport');
                    if (psInput && psInput.offsetParent !== null) {
                        psInput.value = optionValue;
                        psInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    if (csInput && csInput.offsetParent !== null) {
                        csInput.value = optionValue;
                        csInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                } else {
                    // Handle other text inputs normally
                    const input = document.getElementById(optionKey.replace(/_/g, '-'));
                    if (input && input.type === 'text') {
                        input.value = optionValue;
                    }
                }
            });
        }
        
        showNotificationPopup(`✓ Loaded: ${recipeName} - modify parameters and generate`, 'success');
        
    } catch (error) {
        console.error('Failed to load from history:', error);
        alert('Failed to load from history');
    }
}

// Regenerate from history
async function regenerateFromHistory(index) {
    try {
        const response = await fetch(`/api/history/${index}/regenerate`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (!data.success) {
            alert('Failed to load history entry');
            return;
        }
        
        // Close history modal
        document.getElementById('history-modal').classList.remove('active');
        
        // Find and select the recipe
        const recipeName = data.recipe_name;
        let found = false;
        let recipeCategory = null;
        
        for (const [category, categoryRecipes] of Object.entries(categories)) {
            const recipe = categoryRecipes.find(r => r.name === recipeName);
            if (recipe) {
                recipeCategory = category;
                found = true;
                break;
            }
        }
        
        if (!found) {
            alert(`Recipe '${recipeName}' not found. It may have been deleted.`);
            return;
        }
        
        showNotificationPopup(`🔄 Regenerating: ${recipeName}...`, 'info');
        
        // Directly submit payload generation with stored parameters and preprocessing selections
        const generateResponse = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: recipeCategory,
                recipe: recipeName,
                parameters: data.parameters,
                preprocessing_selections: data.preprocessing_selections || {},
                build_options: data.build_options || {}
            })
        });
        
        const generateData = await generateResponse.json();
        
        // Check for error (API returns session_id on success, error on failure)
        if (generateData.error) {
            showNotificationPopup(`✗ Generation failed: ${generateData.error}`, 'error');
            return;
        }
        
        if (!generateData.session_id) {
            showNotificationPopup(`✗ Generation failed: No session ID returned`, 'error');
            return;
        }
        
        // Show build modal and start polling
        const buildModal = document.getElementById('build-modal');
        const stepsContainer = document.getElementById('build-steps-container');
        const resultContainer = document.getElementById('build-result');
        const closeBtn = document.getElementById('close-build-btn');
        
        stepsContainer.innerHTML = '';
        resultContainer.innerHTML = '';
        closeBtn.style.display = 'none';
        buildModal.classList.add('active');
        
        // Poll for build status
        pollBuildStatus(generateData.session_id);
        
    } catch (error) {
        console.error('Failed to regenerate from history:', error);
        alert('Failed to regenerate from history');
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== PowerShell Obfuscator Functions =====

// Global variable to track current loaded filename
let currentPsFilename = null;
let currentLoadedPath = null;

// Show PowerShell Obfuscator modal
async function showObfuscatePsModal() {
    const modal = document.getElementById('obfuscate-ps-modal');
    const inputTextarea = document.getElementById('obfuscate-ps-input');
    const outputSection = document.getElementById('obfuscate-ps-output-section');
    const loadingDiv = document.getElementById('obfuscate-ps-loading');
    const levelSelect = document.getElementById('obfuscate-ps-level');
    const pathInput = document.getElementById('obfuscate-ps-file-path');

    // Always start at main view
    showPsObfMainView();

    // Reset modal state
    inputTextarea.value = '';
    outputSection.style.display = 'none';
    loadingDiv.style.display = 'none';
    currentPsFilename = null;
    currentLoadedPath = null;
    pathInput.value = '';
    
    // Load obfuscation methods from YAML
    try {
        const response = await fetch('/api/ps-obfuscation-methods');
        const data = await response.json();
        
        // Populate dropdown with None option as default, then methods
        levelSelect.innerHTML = '<option value="">None - No obfuscation</option>' + 
            data.methods.map(m => 
                `<option value="${m.name}">${m.name}</option>`
            ).join('');
    } catch (error) {
        console.error('Failed to load obfuscation methods:', error);
        showNotificationPopup('Failed to load obfuscation methods', 'error');
        return;
    }
    
    // Load PS cradles for the dropdown
    try {
        const response = await fetch('/api/ps-cradles');
        const data = await response.json();
        const cradleSelect = document.getElementById('obfuscate-ps-cradle-method');
        
        if (data.cradles && data.cradles.ps1) {
            cradleSelect.innerHTML = data.cradles.ps1.map(c => 
                `<option value="${c.name}">${c.name}</option>`
            ).join('');
        }
    } catch (error) {
        console.error('Failed to load PS cradles:', error);
    }
    
    // Load obfuscation methods for cradle obfuscation dropdown
    try {
        const response = await fetch('/api/ps-obfuscation-methods');
        const data = await response.json();
        const cradleObfSelect = document.getElementById('obfuscate-ps-cradle-obf-method');
        
        cradleObfSelect.innerHTML = '<option value="">None</option>' + 
            data.methods.map(m => 
                `<option value="${m.name}">${m.name}</option>`
            ).join('');
    } catch (error) {
        console.error('Failed to load obfuscation methods for cradle:', error);
    }
    
    // Populate lhost with global.lhost if available
    const cradleLhostInput = document.getElementById('obfuscate-ps-cradle-lhost');
    if (cradleLhostInput) {
        const globalLhost = getDefaultLhost() || '127.0.0.1';
        cradleLhostInput.value = globalLhost;
    }
    
    // Show modal
    modal.classList.add('active');
    
    // Focus on input
    setTimeout(() => inputTextarea.focus(), 100);
}

// Handle file upload via browse button
async function handlePsFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    await loadPsFile(file);
}

// Handle drag over
function handlePsDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    const dropzone = document.getElementById('obfuscate-ps-dropzone');
    dropzone.classList.add('drag-over');
}

// Handle drag leave
function handlePsDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    const dropzone = document.getElementById('obfuscate-ps-dropzone');
    dropzone.classList.remove('drag-over');
}

// Handle drop
async function handlePsDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const dropzone = document.getElementById('obfuscate-ps-dropzone');
    dropzone.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length === 0) return;
    
    const file = files[0];
    
    // Validate file type
    if (!file.name.endsWith('.ps1') && !file.name.endsWith('.txt')) {
        showNotificationPopup('Please drop a .ps1 or .txt file', 'error');
        return;
    }
    
    await loadPsFile(file);
}

// Load file content and set filename
async function loadPsFile(file) {
    try {
        const content = await file.text();
        const inputTextarea = document.getElementById('obfuscate-ps-input');
        const pathInput = document.getElementById('obfuscate-ps-file-path');
        
        inputTextarea.value = content;
        currentPsFilename = file.name;
        
        // Show filename in path input if available
        if (file.path) {
            pathInput.value = file.path;
            currentLoadedPath = file.path;
        } else {
            pathInput.value = file.name;
            currentLoadedPath = file.name;
        }
        
        showNotificationPopup(`Loaded ${file.name}`, 'success');
    } catch (error) {
        console.error('Failed to load file:', error);
        showNotificationPopup('Failed to load file', 'error');
    }
}

// Load file from path (typed in path input)
async function loadPsFileFromPath() {
    const pathInput = document.getElementById('obfuscate-ps-file-path');
    const path = pathInput.value.trim();
    
    if (!path) {
        return;
    }
    
    try {
        const response = await fetch('/api/read-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: path })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to read file');
        }
        
        const inputTextarea = document.getElementById('obfuscate-ps-input');
        inputTextarea.value = data.content;
        
        // Extract filename from path
        const filename = path.split('/').pop().split('\\\\').pop();
        currentPsFilename = filename;
        currentLoadedPath = path;
        
        showNotificationPopup(`Loaded ${filename}`, 'success');
    } catch (error) {
        console.error('Failed to load file from path:', error);
        showNotificationPopup(error.message || 'Failed to load file', 'error');
    }
}

// Generate obfuscated PowerShell
async function generateObfuscatedPs() {
    const inputTextarea = document.getElementById('obfuscate-ps-input');
    const levelSelect = document.getElementById('obfuscate-ps-level');
    const wrapperToggle = document.getElementById('obfuscate-ps-wrapper-toggle');
    const outputSection = document.getElementById('obfuscate-ps-output-section');
    const outputDiv = document.getElementById('obfuscate-ps-output');
    const loadingDiv = document.getElementById('obfuscate-ps-loading');
    const generateBtn = document.getElementById('obfuscate-ps-generate-btn');
    
    const psCommand = inputTextarea.value.trim();
    const method = levelSelect.value;
    const addWrapper = wrapperToggle.checked;
    
    // Validate input
    if (!psCommand) {
        showNotificationPopup('Please enter a PowerShell command', 'error');
        return;
    }
    
    // Show loading, hide output
    outputSection.style.display = 'none';
    loadingDiv.style.display = 'flex';
    generateBtn.disabled = true;
    
    try {
        const response = await fetch('/api/obfuscate-ps', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: psCommand,
                method: method,
                add_wrapper: addWrapper
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Obfuscation failed');
        }
        
        // Display obfuscated code with syntax highlighting
        outputDiv.innerHTML = `<pre class="line-numbers"><code class="language-powershell">${escapeHtml(data.obfuscated)}</code></pre>`;
        
        // Re-add copy button after innerHTML replacement
        const copyBtn = document.createElement('button');
        copyBtn.id = 'obfuscate-ps-copy-btn';
        copyBtn.className = 'btn btn-secondary btn-sm obfuscate-ps-copy-btn-positioned';
        copyBtn.innerHTML = '<span class="btn-icon">📋</span> Copy';
        copyBtn.addEventListener('click', copyObfuscatedPs);
        outputDiv.appendChild(copyBtn);
        
        // Apply syntax highlighting
        Prism.highlightAllUnder(outputDiv);
        
        // Set filename for download
        const filenameInput = document.getElementById('obfuscate-ps-download-filename');
        if (currentPsFilename) {
            // If loaded from file, append "-o" before extension
            const lastDot = currentPsFilename.lastIndexOf('.');
            if (lastDot > 0) {
                const name = currentPsFilename.substring(0, lastDot);
                const ext = currentPsFilename.substring(lastDot);
                filenameInput.value = `${name}-o${ext}`;
            } else {
                filenameInput.value = `${currentPsFilename}-o.ps1`;
            }
        } else {
            // If typed manually, leave empty (user must provide filename)
            filenameInput.value = '';
        }
        
        // Show output section
        loadingDiv.style.display = 'none';
        outputSection.style.display = 'flex';
        
        const methodName = method || 'None';
        const action = method ? 'obfuscated' : 'processed';
        showNotificationPopup(`PowerShell ${action} with ${methodName}!`, 'success');
        
    } catch (error) {
        console.error('Obfuscation error:', error);
        loadingDiv.style.display = 'none';
        showNotificationPopup(error.message || 'Failed to obfuscate PowerShell', 'error');
    } finally {
        generateBtn.disabled = false;
    }
}

// Copy obfuscated PowerShell to clipboard
async function copyObfuscatedPs() {
    const outputDiv = document.getElementById('obfuscate-ps-output');
    const codeElement = outputDiv.querySelector('code');
    
    if (!codeElement) {
        showNotificationPopup('No obfuscated code to copy', 'error');
        return;
    }
    
    const code = codeElement.textContent;
    
    try {
        await navigator.clipboard.writeText(code);
        showNotificationPopup('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy:', error);
        showNotificationPopup('Failed to copy to clipboard', 'error');
    }
}

// Download obfuscated PowerShell as file (save to output_dir)
async function downloadObfuscatedPs() {
    const outputDiv = document.getElementById('obfuscate-ps-output');
    const codeElement = outputDiv.querySelector('code');
    const filenameInput = document.getElementById('obfuscate-ps-download-filename');
    const downloadBtn = document.getElementById('obfuscate-ps-download-btn');
    const statusDiv = document.getElementById('obfuscate-ps-download-status');
    const cradleToggle = document.getElementById('obfuscate-ps-cradle-toggle');
    const cradleMethodSelect = document.getElementById('obfuscate-ps-cradle-method');
    
    if (!codeElement) {
        showNotificationPopup('No obfuscated code to download', 'error');
        return;
    }
    
    const code = codeElement.textContent;
    let filename = filenameInput.value.trim();
    
    // Validate filename
    if (!filename) {
        showNotificationPopup('Please enter a filename', 'error');
        filenameInput.focus();
        return;
    }
    
    // Ensure .ps1 extension
    if (!filename.endsWith('.ps1')) {
        filename += '.ps1';
    }
    
    // Disable button during save
    downloadBtn.disabled = true;
    statusDiv.style.display = 'none';
    
    try {
        // Save to output_dir on server
        const response = await fetch('/api/obfuscate-ps-save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: code,
                filename: filename
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to save file');
        }
        
        let statusMessage = `✓ Saved to: ${data.path}`;
        
        // Generate cradle if checkbox is checked
        if (cradleToggle && cradleToggle.checked) {
            const cradleMethod = cradleMethodSelect.value;
            const cradleObfMethod = document.getElementById('obfuscate-ps-cradle-obf-method').value;
            const cradleLhost = document.getElementById('obfuscate-ps-cradle-lhost').value.trim();
            const cradleLport = document.getElementById('obfuscate-ps-cradle-lport').value;
            
            if (!cradleLhost) {
                statusMessage += '\n⚠ Skipped cradle: LHOST is required';
            } else if (cradleMethod) {
                try {
                    const cradleResponse = await fetch('/api/obfuscate-ps-generate-cradle', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            filename: filename,
                            cradle_method: cradleMethod,
                            cradle_obf_method: cradleObfMethod,
                            lhost: cradleLhost,
                            lport: parseInt(cradleLport) || 80
                        })
                    });
                    
                    const cradleData = await cradleResponse.json();
                    
                    if (cradleResponse.ok) {
                        // Display cradle in code block
                        const cradleOutputSection = document.getElementById('obfuscate-ps-cradle-output-section');
                        const cradleOutputDiv = document.getElementById('obfuscate-ps-cradle-output');
                        
                        cradleOutputDiv.innerHTML = `<pre class="line-numbers"><code class="language-powershell">${escapeHtml(cradleData.cradle_code)}</code></pre>`;
                        
                        // Re-add copy button for cradle
                        const cradleCopyBtn = document.createElement('button');
                        cradleCopyBtn.id = 'obfuscate-ps-cradle-copy-btn';
                        cradleCopyBtn.className = 'btn btn-secondary btn-sm obfuscate-ps-copy-btn-positioned';
                        cradleCopyBtn.innerHTML = '<span class="btn-icon">📋</span> Copy';
                        cradleCopyBtn.addEventListener('click', function() {
                            const cradleCode = cradleOutputDiv.querySelector('code');
                            if (cradleCode) {
                                navigator.clipboard.writeText(cradleCode.textContent);
                                showNotificationPopup('Cradle copied to clipboard!', 'success');
                            }
                        });
                        cradleOutputDiv.appendChild(cradleCopyBtn);
                        
                        // Apply syntax highlighting
                        Prism.highlightAllUnder(cradleOutputDiv);
                        
                        // Show cradle section
                        cradleOutputSection.style.display = 'block';
                        
                        statusMessage += '\n✓ Cradle generated successfully';
                    } else {
                        statusMessage += `\n✗ Cradle generation failed: ${cradleData.error}`;
                    }
                } catch (cradleError) {
                    console.error('Failed to generate cradle:', cradleError);
                    statusMessage += `\n✗ Cradle generation failed: ${cradleError.message}`;
                }
            }
        }
        
        // Show success in panel (replace \n with <br> for HTML line breaks)
        statusDiv.innerHTML = statusMessage.replace(/\n/g, '<br>');
        statusDiv.style.display = 'block';
        statusDiv.style.borderColor = 'var(--teal)';
        statusDiv.style.color = 'var(--teal)';
    } catch (error) {
        console.error('Failed to save file:', error);
        statusDiv.textContent = `✗ Error: ${error.message}`;
        statusDiv.style.display = 'block';
        statusDiv.style.borderColor = 'var(--red)';
        statusDiv.style.color = 'var(--red)';
    } finally {
        downloadBtn.disabled = false;
    }
}

// Settings Functions
function showSettings() {
    // Load current settings from localStorage
    loadSettings();
    document.getElementById('settings-modal').classList.add('active');
}

function loadSettings() {
    const defaultLhost = localStorage.getItem('paygen_default_lhost') || '';
    document.getElementById('default-lhost').value = defaultLhost;
    const defaultOutputDir = localStorage.getItem('paygen_default_output_dir') || '';
    document.getElementById('default-output-dir').value = defaultOutputDir;
}

function saveSettings() {
    const defaultLhost = document.getElementById('default-lhost').value.trim();
    const defaultOutputDir = document.getElementById('default-output-dir').value.trim();

    // Close modal first
    document.getElementById('settings-modal').classList.remove('active');

    // Save LHOST
    const messages = [];
    if (defaultLhost) {
        localStorage.setItem('paygen_default_lhost', defaultLhost);
        messages.push(`LHOST: ${defaultLhost}`);
    } else {
        localStorage.removeItem('paygen_default_lhost');
    }

    // Save output directory
    if (defaultOutputDir) {
        localStorage.setItem('paygen_default_output_dir', defaultOutputDir);
        messages.push(`Output dir: ${defaultOutputDir}`);
    } else {
        localStorage.removeItem('paygen_default_output_dir');
    }

    if (messages.length > 0) {
        showNotificationPopup(`Settings saved - ${messages.join(', ')}`, 'success');
    } else {
        showNotificationPopup('Settings cleared', 'success');
    }
}

function getDefaultLhost() {
    return localStorage.getItem('paygen_default_lhost') || '';
}

function getDefaultOutputDir() {
    return localStorage.getItem('paygen_default_output_dir') || '';
}

function processParameterDefault(defaultValue, paramName) {
    // Process template substitutions in default values
    if (typeof defaultValue !== 'string') {
        return defaultValue;
    }

    let processed = defaultValue;

    // Replace {{ global.lhost }} with the actual global LHOST setting
    if (processed.includes('{{ global.lhost }}') || processed.includes('{{global.lhost}}')) {
        const globalLhost = getDefaultLhost() || '127.0.0.1';
        processed = processed.replace(/\{\{\s*global\.lhost\s*\}\}/g, globalLhost);
    }

    // Replace {{ global.output_dir }} with the actual global output directory setting
    if (processed.includes('{{ global.output_dir }}') || processed.includes('{{global.output_dir}}')) {
        const globalOutputDir = getDefaultOutputDir() || '/tmp/paygen-output';
        processed = processed.replace(/\{\{\s*global\.output_dir\s*\}\}/g, globalOutputDir);
    }

    return processed;
}


// ===== RECIPE EDITOR =====

let editorMode = 'create'; // 'create' or 'edit'
let editorOriginalCategory = '';
let editorOriginalName = '';
let categoryHighlightIndex = -1;

// Category combobox helpers
function populateCategoryDropdown(filter) {
    const dropdown = document.getElementById('category-dropdown');
    dropdown.innerHTML = '';
    categoryHighlightIndex = -1;
    if (!categories) return;

    const cats = Object.keys(categories).sort();
    const filterLower = (filter || '').toLowerCase();
    const matched = filterLower
        ? cats.filter(c => c.toLowerCase().includes(filterLower))
        : cats;

    if (matched.length === 0) {
        const li = document.createElement('li');
        li.classList.add('no-match');
        li.textContent = filter ? 'No matching categories' : 'No categories yet';
        dropdown.appendChild(li);
        return;
    }

    matched.forEach(cat => {
        const li = document.createElement('li');
        li.textContent = cat;
        li.addEventListener('mousedown', (e) => {
            e.preventDefault(); // prevent input blur
            document.getElementById('editor-category').value = cat;
            closeCategoryDropdown();
        });
        dropdown.appendChild(li);
    });
}

function openCategoryDropdown() {
    const wrapper = document.getElementById('category-combobox');
    wrapper.classList.add('open');
    const input = document.getElementById('editor-category');
    populateCategoryDropdown(input.value);
}

function closeCategoryDropdown() {
    const wrapper = document.getElementById('category-combobox');
    wrapper.classList.remove('open');
    categoryHighlightIndex = -1;
}

function highlightCategoryItem(index) {
    const items = document.querySelectorAll('#category-dropdown li:not(.no-match)');
    items.forEach(li => li.classList.remove('highlighted'));
    if (index >= 0 && index < items.length) {
        items[index].classList.add('highlighted');
        items[index].scrollIntoView({ block: 'nearest' });
    }
}

// Set up combobox event listeners (called once on load)
function initCategoryCombobox() {
    const input = document.getElementById('editor-category');
    const toggle = document.querySelector('#category-combobox .combobox-toggle');
    const wrapper = document.getElementById('category-combobox');

    input.addEventListener('focus', () => openCategoryDropdown());
    input.addEventListener('blur', () => closeCategoryDropdown());
    input.addEventListener('input', () => {
        openCategoryDropdown();
        populateCategoryDropdown(input.value);
    });

    input.addEventListener('keydown', (e) => {
        const items = document.querySelectorAll('#category-dropdown li:not(.no-match)');
        if (!wrapper.classList.contains('open') || items.length === 0) {
            if (e.key === 'ArrowDown') openCategoryDropdown();
            return;
        }

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            categoryHighlightIndex = Math.min(categoryHighlightIndex + 1, items.length - 1);
            highlightCategoryItem(categoryHighlightIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            categoryHighlightIndex = Math.max(categoryHighlightIndex - 1, 0);
            highlightCategoryItem(categoryHighlightIndex);
        } else if (e.key === 'Enter' && categoryHighlightIndex >= 0) {
            e.preventDefault();
            input.value = items[categoryHighlightIndex].textContent;
            closeCategoryDropdown();
        } else if (e.key === 'Escape') {
            closeCategoryDropdown();
        }
    });

    toggle.addEventListener('mousedown', (e) => {
        e.preventDefault(); // prevent stealing focus from input
        if (wrapper.classList.contains('open')) {
            closeCategoryDropdown();
        } else {
            input.focus();
        }
    });
}

function openEditor(mode, recipeData) {
    editorMode = mode;
    const modal = document.getElementById('recipe-editor-modal');
    const title = document.getElementById('editor-modal-title');

    title.textContent = mode === 'create' ? 'Create Recipe' : 'Edit Recipe';

    // Populate category combobox dropdown
    populateCategoryDropdown();

    if (recipeData) {
        populateEditor(recipeData);
    } else {
        clearEditor();
    }

    // Show first tab
    switchEditorTab('meta');
    modal.classList.add('active');
}

function clearEditor() {
    document.getElementById('editor-name').value = '';
    document.getElementById('editor-category').value = '';
    document.getElementById('editor-description').value = '';
    document.getElementById('editor-platform').value = '';
    document.getElementById('editor-effectiveness').value = 'medium';
    document.getElementById('editor-mitre-tactic').value = '';
    document.getElementById('editor-mitre-technique').value = '';
    document.getElementById('editor-artifacts-list').innerHTML = '';
    document.getElementById('editor-params-list').innerHTML = '';
    document.getElementById('editor-preproc-list').innerHTML = '';
    document.getElementById('editor-output-type').value = 'template';
    document.getElementById('editor-template-ext').value = '.cs';
    document.getElementById('editor-template-code').value = '';
    document.getElementById('editor-command').value = '';
    document.getElementById('editor-compile-enabled').checked = false;
    document.getElementById('editor-compile-command').value = '';
    document.getElementById('editor-launch-instructions').value = '';
    document.getElementById('editor-version-comment').value = editorMode === 'create' ? 'Initial version' : '';
    toggleOutputFields();
    toggleCompileFields();
}

function populateEditor(data) {
    const meta = data.meta || {};
    const mitre = meta.mitre || {};
    const output = data.output || {};
    const compile = output.compile || {};

    document.getElementById('editor-name').value = meta.name || '';
    document.getElementById('editor-category').value = meta.category || '';
    document.getElementById('editor-description').value = meta.description || '';
    document.getElementById('editor-platform').value = meta.platform || '';
    document.getElementById('editor-effectiveness').value = meta.effectiveness || 'medium';
    document.getElementById('editor-mitre-tactic').value = mitre.tactic || '';
    document.getElementById('editor-mitre-technique').value = mitre.technique || '';

    editorOriginalCategory = meta.category || '';
    editorOriginalName = meta.name || '';

    // Artifacts
    const artifactsList = document.getElementById('editor-artifacts-list');
    artifactsList.innerHTML = '';
    (meta.artifacts || []).forEach(a => addArtifactRow(a));

    // Parameters
    const paramsList = document.getElementById('editor-params-list');
    paramsList.innerHTML = '';
    (data.parameters || []).forEach(p => addParamRow(p));

    // Preprocessing
    const preprocList = document.getElementById('editor-preproc-list');
    preprocList.innerHTML = '';
    (data.preprocessing || []).forEach(p => addPreprocRow(p));

    // Output
    document.getElementById('editor-output-type').value = output.type || 'template';
    if (output.type === 'template') {
        document.getElementById('editor-template-ext').value = output.template_ext || '.cs';
        const tmpl = output.template || '';
        document.getElementById('editor-template-code').value = tmpl;
    } else {
        document.getElementById('editor-command').value = output.command || '';
    }

    document.getElementById('editor-compile-enabled').checked = compile.enabled || false;
    document.getElementById('editor-compile-command').value = compile.command || '';
    document.getElementById('editor-launch-instructions').value = output.launch_instructions || '';
    document.getElementById('editor-version-comment').value = '';

    toggleOutputFields();
    toggleCompileFields();
}

function switchEditorTab(tabName) {
    document.querySelectorAll('.editor-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
    document.querySelectorAll('.editor-tab-content').forEach(c => c.classList.toggle('active', c.dataset.tab === tabName));
}

function toggleOutputFields() {
    const type = document.getElementById('editor-output-type').value;
    document.getElementById('editor-template-fields').style.display = type === 'template' ? '' : 'none';
    document.getElementById('editor-command-fields').style.display = type === 'command' ? '' : 'none';
}

function toggleCompileFields() {
    const enabled = document.getElementById('editor-compile-enabled').checked;
    document.getElementById('editor-compile-fields').style.display = enabled ? '' : 'none';
}

// Artifact rows
function addArtifactRow(value) {
    const list = document.getElementById('editor-artifacts-list');
    const div = document.createElement('div');
    div.className = 'editor-list-item';
    div.innerHTML = `
        <div style="display:flex;gap:0.5rem;align-items:center;">
            <input type="text" class="param-form-input artifact-input" value="${escapeHtml(value || '')}" placeholder="Artifact description">
            <button class="editor-list-remove" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    list.appendChild(div);
}

// Parameter rows
function addParamRow(param) {
    const list = document.getElementById('editor-params-list');
    const div = document.createElement('div');
    div.className = 'editor-list-item';
    const p = param || {};
    div.innerHTML = `
        <div class="editor-list-item-header">
            <span class="editor-list-item-title">Parameter</span>
            <button class="editor-list-remove" onclick="this.closest('.editor-list-item').remove()">&times;</button>
        </div>
        <div class="editor-field-row">
            <div class="editor-field"><label>Name *</label><input type="text" class="param-form-input p-name" value="${escapeHtml(p.name || '')}"></div>
            <div class="editor-field"><label>Type</label>
                <select class="param-form-select p-type">
                    <option value="string" ${p.type==='string'?'selected':''}>string</option>
                    <option value="ip" ${p.type==='ip'?'selected':''}>ip</option>
                    <option value="port" ${p.type==='port'?'selected':''}>port</option>
                    <option value="path" ${p.type==='path'?'selected':''}>path</option>
                    <option value="file" ${p.type==='file'?'selected':''}>file</option>
                    <option value="hex" ${p.type==='hex'?'selected':''}>hex</option>
                    <option value="bool" ${p.type==='bool'?'selected':''}>bool</option>
                    <option value="integer" ${p.type==='integer'?'selected':''}>integer</option>
                    <option value="choice" ${p.type==='choice'?'selected':''}>choice</option>
                </select>
            </div>
        </div>
        <div class="editor-field"><label>Description</label><input type="text" class="param-form-input p-desc" value="${escapeHtml(p.description || '')}"></div>
        <div class="editor-field-row">
            <div class="editor-field"><label>Default</label><input type="text" class="param-form-input p-default" value="${escapeHtml(String(p.default || ''))}"></div>
            <div class="editor-field"><label>Required</label>
                <select class="param-form-select p-required">
                    <option value="true" ${p.required===true||p.required==='true'?'selected':''}>Yes</option>
                    <option value="false" ${p.required===false||p.required==='false'?'selected':''}>No</option>
                </select>
            </div>
        </div>
        ${p.required_for ? `<div class="editor-field"><label>Required For</label><input type="text" class="param-form-input p-required-for" value="${escapeHtml(p.required_for || '')}"></div>` : ''}
    `;
    list.appendChild(div);
}

// Preprocessing rows
function addPreprocRow(step) {
    const list = document.getElementById('editor-preproc-list');
    const div = document.createElement('div');
    div.className = 'editor-list-item';
    const s = step || {};
    div.innerHTML = `
        <div class="editor-list-item-header">
            <span class="editor-list-item-title">Step: ${escapeHtml(s.name || 'New Step')}</span>
            <button class="editor-list-remove" onclick="this.closest('.editor-list-item').remove()">&times;</button>
        </div>
        <div class="editor-field-row">
            <div class="editor-field"><label>Type</label>
                <select class="param-form-select pp-type">
                    <option value="command" ${s.type==='command'?'selected':''}>command</option>
                    <option value="script" ${s.type==='script'?'selected':''}>script</option>
                    <option value="shellcode" ${s.type==='shellcode'?'selected':''}>shellcode</option>
                    <option value="option" ${s.type==='option'?'selected':''}>option</option>
                </select>
            </div>
            <div class="editor-field"><label>Name</label><input type="text" class="param-form-input pp-name" value="${escapeHtml(s.name || '')}"></div>
        </div>
        <div class="editor-field"><label>Output Variable</label><input type="text" class="param-form-input pp-output-var" value="${escapeHtml(s.output_var || '')}"></div>
        ${s.type === 'command' ? `<div class="editor-field"><label>Command</label><textarea class="param-form-input pp-command" rows="2">${escapeHtml(s.command || '')}</textarea></div>` : ''}
        ${s.type === 'script' ? `<div class="editor-field"><label>Script</label><input type="text" class="param-form-input pp-script" value="${escapeHtml(s.script || '')}"></div>` : ''}
    `;
    list.appendChild(div);
}

function collectEditorData() {
    const meta = {
        name: document.getElementById('editor-name').value.trim(),
        category: document.getElementById('editor-category').value.trim() || 'Misc',
        description: document.getElementById('editor-description').value.trim(),
        effectiveness: document.getElementById('editor-effectiveness').value
    };

    const platform = document.getElementById('editor-platform').value;
    if (platform) meta.platform = platform;

    const tactic = document.getElementById('editor-mitre-tactic').value.trim();
    const technique = document.getElementById('editor-mitre-technique').value.trim();
    if (tactic || technique) {
        meta.mitre = {};
        if (tactic) meta.mitre.tactic = tactic;
        if (technique) meta.mitre.technique = technique;
    }

    // Artifacts
    const artifacts = [];
    document.querySelectorAll('#editor-artifacts-list .artifact-input').forEach(inp => {
        const v = inp.value.trim();
        if (v) artifacts.push(v);
    });
    if (artifacts.length) meta.artifacts = artifacts;

    // Parameters
    const parameters = [];
    document.querySelectorAll('#editor-params-list .editor-list-item').forEach(item => {
        const p = {
            name: item.querySelector('.p-name').value.trim(),
            type: item.querySelector('.p-type').value,
            description: item.querySelector('.p-desc')?.value.trim() || '',
            required: item.querySelector('.p-required').value === 'true'
        };
        const def = item.querySelector('.p-default')?.value.trim();
        if (def !== '') {
            // Try to parse as number for port/integer types
            if (p.type === 'port' || p.type === 'integer') {
                p.default = parseInt(def, 10) || def;
            } else {
                p.default = def;
            }
        }
        const reqFor = item.querySelector('.p-required-for');
        if (reqFor && reqFor.value.trim()) {
            p.required_for = reqFor.value.trim();
        }
        if (p.name) parameters.push(p);
    });

    // Preprocessing
    const preprocessing = [];
    document.querySelectorAll('#editor-preproc-list .editor-list-item').forEach(item => {
        const s = {
            type: item.querySelector('.pp-type').value,
            name: item.querySelector('.pp-name').value.trim(),
            output_var: item.querySelector('.pp-output-var')?.value.trim() || ''
        };
        const cmd = item.querySelector('.pp-command');
        if (cmd) s.command = cmd.value.trim();
        const script = item.querySelector('.pp-script');
        if (script) s.script = script.value.trim();
        if (s.name || s.type) preprocessing.push(s);
    });

    // Output
    const outputType = document.getElementById('editor-output-type').value;
    const output = { type: outputType };

    if (outputType === 'template') {
        output.template_ext = document.getElementById('editor-template-ext').value;
        output.template = document.getElementById('editor-template-code').value;
    } else {
        output.command = document.getElementById('editor-command').value.trim();
    }

    if (document.getElementById('editor-compile-enabled').checked) {
        output.compile = {
            enabled: true,
            command: document.getElementById('editor-compile-command').value.trim()
        };
    }

    const launchInstr = document.getElementById('editor-launch-instructions').value.trim();
    if (launchInstr) output.launch_instructions = launchInstr;

    return { meta, parameters, preprocessing, output };
}

async function saveRecipe() {
    const recipeData = collectEditorData();
    const comment = document.getElementById('editor-version-comment').value.trim() || (editorMode === 'create' ? 'Initial version' : 'Updated');

    try {
        let resp;
        if (editorMode === 'create') {
            resp = await fetch('/api/recipes/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipe: recipeData, _comment: comment })
            });
        } else {
            resp = await fetch(`/api/recipe/${encodeURIComponent(editorOriginalCategory)}/${encodeURIComponent(editorOriginalName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipe: recipeData, _comment: comment })
            });
        }

        const result = await resp.json();
        if (resp.ok && result.success) {
            closeModal('recipe-editor-modal');
            showNotificationPopup(editorMode === 'create' ? 'Recipe created!' : 'Recipe updated!', 'success');
            await loadRecipes();
            // Re-select the recipe
            const newCat = recipeData.meta.category || 'Misc';
            const newName = recipeData.meta.name;
            selectRecipe(newCat, newName);
        } else {
            showNotificationPopup(result.error || 'Failed to save recipe', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error saving recipe: ' + e.message, 'error');
    }
}

async function validateRecipeEditor() {
    const recipeData = collectEditorData();
    try {
        const resp = await fetch('/api/recipes/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe: recipeData })
        });
        const result = await resp.json();
        if (result.valid) {
            showNotificationPopup('Recipe is valid!', 'success');
        } else {
            showNotificationPopup('Validation error: ' + result.error, 'error');
        }
    } catch (e) {
        showNotificationPopup('Validation error: ' + e.message, 'error');
    }
}

async function openEditorForEdit() {
    if (!selectedRecipe) return;
    const cat = selectedRecipe.category || 'Misc';
    const name = selectedRecipe.name;
    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}/raw`);
        const data = await resp.json();
        if (resp.ok) {
            openEditor('edit', data);
        } else {
            showNotificationPopup(data.error || 'Failed to load recipe for editing', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error loading recipe: ' + e.message, 'error');
    }
}

async function deleteCurrentRecipe() {
    if (!selectedRecipe) return;
    if (!confirm(`Delete recipe "${selectedRecipe.name}"? This cannot be undone.`)) return;

    const cat = selectedRecipe.category || 'Misc';
    const name = selectedRecipe.name;
    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}`, { method: 'DELETE' });
        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup('Recipe deleted', 'success');
            selectedRecipe = null;
            await loadRecipes();
            document.getElementById('recipe-details').innerHTML = '<div class="placeholder"><p>Select a recipe to view details</p></div>';
            document.getElementById('code-preview').innerHTML = '<div class="placeholder"><p>Select a recipe to view code</p></div>';
            updateRecipeHeaderActions(null);
        } else {
            showNotificationPopup(result.error || 'Failed to delete', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error deleting recipe: ' + e.message, 'error');
    }
}

// Helper to close modal by ID
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}


// ===== VERSION HISTORY =====

let versionSelectedVersion = null;

async function openVersionHistory() {
    if (!selectedRecipe) return;
    const cat = selectedRecipe.category || 'Misc';
    const name = selectedRecipe.name;

    document.getElementById('version-modal-title').textContent = `Versions - ${name}`;
    document.getElementById('version-detail').style.display = 'none';
    document.getElementById('version-detail-actions').style.display = 'none';
    versionSelectedVersion = null;

    // Show remove button only if multiple versions exist
    const removeBtn = document.getElementById('version-remove-latest-btn');
    if (removeBtn) {
        removeBtn.style.display = (selectedRecipe.version_count || 1) > 1 ? '' : 'none';
    }

    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}/versions`);
        const data = await resp.json();

        if (!resp.ok) {
            showNotificationPopup(data.error || 'Failed to load versions', 'error');
            return;
        }

        const list = document.getElementById('version-list');
        list.innerHTML = '';

        (data.versions || []).forEach(v => {
            const div = document.createElement('div');
            div.className = 'version-item';
            div.dataset.version = v.version;
            div.innerHTML = `
                <div class="version-item-header">
                    <span class="version-item-number">v${v.version}</span>
                    <span class="version-item-timestamp">${v.timestamp || ''}</span>
                </div>
                <div class="version-item-comment">${escapeHtml(v.comment || '')}</div>
            `;
            div.addEventListener('click', () => selectVersion(cat, name, v.version, div));
            list.appendChild(div);
        });

        document.getElementById('version-history-modal').classList.add('active');
    } catch (e) {
        showNotificationPopup('Error loading versions: ' + e.message, 'error');
    }
}

async function selectVersion(cat, name, version, element) {
    // Highlight selection
    document.querySelectorAll('.version-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    versionSelectedVersion = version;

    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}/versions/${version}`);
        const data = await resp.json();

        if (!resp.ok) {
            showNotificationPopup(data.error || 'Failed to load version', 'error');
            return;
        }

        const detail = document.getElementById('version-detail');
        const code = document.getElementById('version-detail-code');
        // Show as formatted YAML-like JSON
        code.textContent = JSON.stringify(data, null, 2);
        detail.style.display = '';
        document.getElementById('version-detail-actions').style.display = '';
    } catch (e) {
        showNotificationPopup('Error loading version: ' + e.message, 'error');
    }
}

async function useVersion() {
    if (!selectedRecipe || !versionSelectedVersion) return;
    const cat = selectedRecipe.category || 'Misc';
    const name = selectedRecipe.name;
    const totalVersions = selectedRecipe.version_count || 1;

    // If selecting the latest version, just reset to default
    if (versionSelectedVersion >= totalVersions) {
        selectedVersion = null;
        closeModal('version-history-modal');
        showNotificationPopup('Using latest version', 'info');
        return;
    }

    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}/versions/${versionSelectedVersion}`);
        const data = await resp.json();

        if (!resp.ok) {
            showNotificationPopup(data.error || 'Failed to load version', 'error');
            return;
        }

        // Update selectedRecipe with version-specific data
        const meta = data.meta || {};
        const mitre = meta.mitre || {};
        selectedRecipe = {
            ...selectedRecipe,
            name: meta.name || selectedRecipe.name,
            category: meta.category || selectedRecipe.category,
            description: meta.description || '',
            effectiveness: meta.effectiveness || 'low',
            platform: meta.platform || null,
            mitre_tactic: mitre.tactic || null,
            mitre_technique: mitre.technique || null,
            artifacts: meta.artifacts || [],
            parameters: data.parameters || [],
            preprocessing: data.preprocessing || [],
            output: data.output || {},
            launch_instructions: (data.output || {}).launch_instructions || null
        };
        selectedVersion = versionSelectedVersion;

        closeModal('version-history-modal');
        renderRecipeDetails(selectedRecipe);
        showNotificationPopup(`Using version ${versionSelectedVersion}`, 'success');
    } catch (e) {
        showNotificationPopup('Error loading version: ' + e.message, 'error');
    }
}


async function removeLatestVersion() {
    if (!selectedRecipe) return;
    const cat = selectedRecipe.category || 'Misc';
    const name = selectedRecipe.name;
    const totalVersions = selectedRecipe.version_count || 1;

    if (totalVersions <= 1) {
        showNotificationPopup('Cannot remove the only version', 'error');
        return;
    }

    if (!confirm(`Remove version ${totalVersions} from "${name}"? This cannot be undone.`)) return;

    try {
        const resp = await fetch(`/api/recipe/${encodeURIComponent(cat)}/${encodeURIComponent(name)}/versions/latest`, {
            method: 'DELETE'
        });
        const data = await resp.json();

        if (!resp.ok) {
            showNotificationPopup(data.error || 'Failed to remove version', 'error');
            return;
        }

        showNotificationPopup(`Version ${totalVersions} removed`, 'success');
        closeModal('version-history-modal');

        // Reset version selection and reload
        selectedVersion = null;
        await loadRecipes();
        selectRecipe(cat, name);
    } catch (e) {
        showNotificationPopup('Error removing version: ' + e.message, 'error');
    }
}

// ===== SHELLCODE MANAGER =====

let scEditorMode = 'create'; // 'create' or 'edit'
let scEditorOriginalName = '';

function showShellcodeManager() {
    const modal = document.getElementById('shellcode-mgr-modal');
    document.getElementById('shellcode-mgr-title').textContent = 'Shellcode Manager';
    showScListView();
    modal.classList.add('active');
    loadShellcodeList();
}

async function loadShellcodeList() {
    const container = document.getElementById('shellcode-mgr-list');
    container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">Loading...</div>';

    try {
        const resp = await fetch('/api/shellcodes');
        const data = await resp.json();

        if (!data.shellcodes || data.shellcodes.length === 0) {
            container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">No shellcodes configured. Click "+ New Shellcode" to create one.</div>';
            return;
        }

        let html = '';
        data.shellcodes.forEach(sc => {
            const paramCount = sc.parameters ? sc.parameters.length : 0;
            const hasListener = sc.has_listener;
            html += `
                <div class="shellcode-mgr-card">
                    <div class="shellcode-mgr-card-info">
                        <div class="shellcode-mgr-card-name">${escapeHtml(sc.name)}</div>
                        <div class="shellcode-mgr-card-meta">
                            <span>${paramCount} param${paramCount !== 1 ? 's' : ''}</span>
                            ${hasListener ? '<span style="color:var(--green);">listener</span>' : ''}
                        </div>
                    </div>
                    <div class="shellcode-mgr-card-actions">
                        <button class="btn btn-primary btn-sm" onclick="openScGenerate('${escapeHtml(sc.name).replace(/'/g, "\\'")}')">Generate</button>
                        <button class="btn btn-secondary btn-sm" onclick="openScEditor('edit', '${escapeHtml(sc.name).replace(/'/g, "\\'")}')">Edit</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteShellcode('${escapeHtml(sc.name).replace(/'/g, "\\'")}')">Delete</button>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<div style="color:var(--red);text-align:center;padding:2rem;">Error loading shellcodes: ${escapeHtml(e.message)}</div>`;
    }
}

function showScListView() {
    document.getElementById('shellcode-mgr-list-view').style.display = '';
    document.getElementById('shellcode-mgr-editor-view').style.display = 'none';
    document.getElementById('shellcode-mgr-generate-view').style.display = 'none';
    document.getElementById('shellcode-mgr-title').textContent = 'Shellcode Manager';
}

function showScEditorView() {
    document.getElementById('shellcode-mgr-list-view').style.display = 'none';
    document.getElementById('shellcode-mgr-editor-view').style.display = '';
    document.getElementById('shellcode-mgr-generate-view').style.display = 'none';
}

function showScGenerateView() {
    document.getElementById('shellcode-mgr-list-view').style.display = 'none';
    document.getElementById('shellcode-mgr-editor-view').style.display = 'none';
    document.getElementById('shellcode-mgr-generate-view').style.display = '';
}

// Editor functions
async function openScEditor(mode, name) {
    scEditorMode = mode;
    scEditorOriginalName = mode === 'edit' ? name : '';
    document.getElementById('shellcode-mgr-title').textContent = mode === 'create' ? 'New Shellcode' : 'Edit Shellcode';
    clearScEditor();

    if (mode === 'edit' && name) {
        try {
            const resp = await fetch(`/api/shellcode/${encodeURIComponent(name)}/raw`);
            const data = await resp.json();
            if (data.error) {
                showNotificationPopup(data.error, 'error');
                return;
            }
            populateScEditor(data);
        } catch (e) {
            showNotificationPopup('Error loading shellcode: ' + e.message, 'error');
            return;
        }
    }

    showScEditorView();
}

function clearScEditor() {
    document.getElementById('sc-editor-name').value = '';
    document.getElementById('sc-editor-command').value = '';
    document.getElementById('sc-editor-listener').value = '';
    document.getElementById('sc-editor-params-list').innerHTML = '';
}

function populateScEditor(data) {
    document.getElementById('sc-editor-name').value = data.name || '';
    document.getElementById('sc-editor-command').value = data.shellcode || '';
    document.getElementById('sc-editor-listener').value = data.listener || '';

    const paramsList = document.getElementById('sc-editor-params-list');
    paramsList.innerHTML = '';
    (data.parameters || []).forEach(p => addScParamRow(p));
}

function addScParamRow(param) {
    const list = document.getElementById('sc-editor-params-list');
    const div = document.createElement('div');
    div.className = 'editor-list-item';
    const p = param || {};
    div.innerHTML = `
        <div class="editor-list-item-header">
            <span class="editor-list-item-title">Parameter</span>
            <button class="editor-list-remove" onclick="this.closest('.editor-list-item').remove()">&times;</button>
        </div>
        <div class="editor-field-row">
            <div class="editor-field"><label>Name *</label><input type="text" class="param-form-input sc-p-name" value="${escapeHtml(p.name || '')}"></div>
            <div class="editor-field"><label>Type</label>
                <select class="param-form-select sc-p-type">
                    <option value="string" ${p.type==='string'?'selected':''}>string</option>
                    <option value="ip" ${p.type==='ip'?'selected':''}>ip</option>
                    <option value="port" ${p.type==='port'?'selected':''}>port</option>
                    <option value="path" ${p.type==='path'?'selected':''}>path</option>
                    <option value="file" ${p.type==='file'?'selected':''}>file</option>
                    <option value="hex" ${p.type==='hex'?'selected':''}>hex</option>
                    <option value="integer" ${p.type==='integer'?'selected':''}>integer</option>
                </select>
            </div>
        </div>
        <div class="editor-field"><label>Description</label><input type="text" class="param-form-input sc-p-desc" value="${escapeHtml(p.description || '')}"></div>
        <div class="editor-field-row">
            <div class="editor-field"><label>Default</label><input type="text" class="param-form-input sc-p-default" value="${escapeHtml(String(p.default !== undefined ? p.default : ''))}"></div>
            <div class="editor-field"><label>Required</label>
                <select class="param-form-select sc-p-required">
                    <option value="true" ${p.required===true||p.required==='true'?'selected':''}>Yes</option>
                    <option value="false" ${p.required===false||p.required==='false'||!p.required?'selected':''}>No</option>
                </select>
            </div>
        </div>
    `;
    list.appendChild(div);
}

function collectScEditorData() {
    const name = document.getElementById('sc-editor-name').value.trim();
    const shellcode = document.getElementById('sc-editor-command').value.trim();
    const listener = document.getElementById('sc-editor-listener').value.trim();

    const parameters = [];
    document.querySelectorAll('#sc-editor-params-list .editor-list-item').forEach(item => {
        const p = {
            name: item.querySelector('.sc-p-name').value.trim(),
            type: item.querySelector('.sc-p-type').value,
            description: item.querySelector('.sc-p-desc')?.value.trim() || '',
            required: item.querySelector('.sc-p-required').value === 'true'
        };
        const def = item.querySelector('.sc-p-default')?.value.trim();
        if (def !== '') {
            if (p.type === 'port' || p.type === 'integer') {
                p.default = parseInt(def, 10) || def;
            } else {
                p.default = def;
            }
        }
        if (p.name) parameters.push(p);
    });

    const data = { name, parameters, shellcode };
    if (listener) data.listener = listener;
    return data;
}

async function saveShellcode() {
    const data = collectScEditorData();

    if (!data.name) {
        showNotificationPopup('Shellcode name is required', 'error');
        return;
    }
    if (!data.shellcode) {
        showNotificationPopup('Shellcode command is required', 'error');
        return;
    }

    try {
        let resp;
        if (scEditorMode === 'create') {
            resp = await fetch('/api/shellcodes/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            resp = await fetch(`/api/shellcode/${encodeURIComponent(scEditorOriginalName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup(scEditorMode === 'create' ? 'Shellcode created!' : 'Shellcode updated!', 'success');
            showScListView();
            loadShellcodeList();
        } else {
            showNotificationPopup(result.error || 'Failed to save shellcode', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error saving shellcode: ' + e.message, 'error');
    }
}

async function deleteShellcode(name) {
    if (!confirm(`Delete shellcode "${name}"?`)) return;

    try {
        const resp = await fetch(`/api/shellcode/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup('Shellcode deleted', 'success');
            loadShellcodeList();
        } else {
            showNotificationPopup(result.error || 'Failed to delete shellcode', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error deleting shellcode: ' + e.message, 'error');
    }
}

// Generate functions
async function openScGenerate(name) {
    document.getElementById('shellcode-mgr-title').textContent = `Generate: ${name}`;
    document.getElementById('sc-generate-result').style.display = 'none';
    document.getElementById('sc-generate-btn').dataset.shellcodeName = name;
    document.getElementById('sc-generate-btn').disabled = false;

    const container = document.getElementById('sc-generate-params-container');
    container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:1rem;">Loading parameters...</div>';

    showScGenerateView();

    try {
        const resp = await fetch(`/api/shellcode/${encodeURIComponent(name)}`);
        const sc = await resp.json();

        if (sc.error) {
            container.innerHTML = `<div style="color:var(--red);">${escapeHtml(sc.error)}</div>`;
            return;
        }

        let html = '';
        if (sc.parameters && sc.parameters.length > 0) {
            sc.parameters.forEach(param => {
                const isRequired = param.required || false;
                let defaultVal = param.default !== undefined ? param.default : '';
                defaultVal = processParameterDefault(String(defaultVal), param.name);

                if (param.name.toLowerCase() === 'lhost') {
                    const settingsLhost = getDefaultLhost();
                    if (settingsLhost) defaultVal = settingsLhost;
                }

                html += `
                    <div class="param-form-item">
                        <label class="param-form-label">
                            ${escapeHtml(param.name)}
                            ${isRequired ? '<span class="param-required">*</span>' : ''}
                            <span class="param-type">[${escapeHtml(param.type)}]</span>
                        </label>
                        <input type="text"
                               class="param-form-input"
                               data-sc-param="${escapeHtml(param.name)}"
                               data-type="${escapeHtml(param.type)}"
                               data-required="${isRequired}"
                               value="${escapeHtml(String(defaultVal))}"
                               placeholder="${escapeHtml(param.description || '')}">
                        <div class="param-form-description">${escapeHtml(param.description || '')}</div>
                    </div>
                `;
            });
        } else {
            html = '<div style="color:var(--subtext0);padding:1rem;">This shellcode has no parameters.</div>';
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<div style="color:var(--red);">Error: ${escapeHtml(e.message)}</div>`;
    }
}

async function generateShellcode() {
    const name = document.getElementById('sc-generate-btn').dataset.shellcodeName;
    const generateBtn = document.getElementById('sc-generate-btn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';

    // Collect parameters
    const parameters = {};
    document.querySelectorAll('#sc-generate-params-container [data-sc-param]').forEach(input => {
        parameters[input.dataset.scParam] = input.value.trim();
    });

    try {
        const resp = await fetch('/api/shellcodes/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parameters })
        });

        const result = await resp.json();

        if (resp.ok && result.success) {
            document.getElementById('sc-generate-result').style.display = '';
            document.getElementById('sc-generate-size').textContent = `Size: ${result.size} bytes`;
            document.getElementById('sc-generate-output-hex').value = result.hex;
            document.getElementById('sc-generate-save-filename').value = 'shellcode.bin';
            document.getElementById('sc-generate-save-status').style.display = 'none';

            if (result.listener) {
                document.getElementById('sc-generate-listener-section').style.display = '';
                document.getElementById('sc-generate-listener-cmd').value = result.listener;
            } else {
                document.getElementById('sc-generate-listener-section').style.display = 'none';
            }
        } else {
            showNotificationPopup(result.error || 'Generation failed', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error generating shellcode: ' + e.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate';
    }
}

async function saveGeneratedShellcode() {
    const hex = document.getElementById('sc-generate-output-hex').value;
    const filenameInput = document.getElementById('sc-generate-save-filename');
    const saveBtn = document.getElementById('sc-generate-save-btn');
    const statusDiv = document.getElementById('sc-generate-save-status');

    let filename = filenameInput.value.trim();
    if (!filename) {
        showNotificationPopup('Please enter a filename', 'error');
        filenameInput.focus();
        return;
    }
    if (!hex) {
        showNotificationPopup('No shellcode data to save', 'error');
        return;
    }

    saveBtn.disabled = true;
    statusDiv.style.display = 'none';

    try {
        const resp = await fetch('/api/shellcodes/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hex, filename })
        });

        const result = await resp.json();

        if (resp.ok && result.success) {
            statusDiv.textContent = `Saved to: ${result.path}`;
            statusDiv.style.display = 'block';
            statusDiv.style.borderColor = 'var(--teal)';
            statusDiv.style.color = 'var(--teal)';
        } else {
            statusDiv.textContent = `Error: ${result.error}`;
            statusDiv.style.display = 'block';
            statusDiv.style.borderColor = 'var(--red)';
            statusDiv.style.color = 'var(--red)';
        }
    } catch (e) {
        statusDiv.textContent = `Error: ${e.message}`;
        statusDiv.style.display = 'block';
        statusDiv.style.borderColor = 'var(--red)';
        statusDiv.style.color = 'var(--red)';
    } finally {
        saveBtn.disabled = false;
    }
}

// ===== PS OBFUSCATION METHOD MANAGER =====

let psObfEditorMode = 'create'; // 'create' or 'edit'
let psObfEditorOriginalName = '';

function showPsObfMainView() {
    document.getElementById('ps-obf-main-view').style.display = '';
    document.getElementById('ps-obf-list-view').style.display = 'none';
    document.getElementById('ps-obf-editor-view').style.display = 'none';
    document.getElementById('ps-obf-footer-main').style.display = '';
    document.getElementById('ps-obf-footer-list').style.display = 'none';
    document.getElementById('ps-obf-footer-editor').style.display = 'none';
    document.getElementById('ps-obf-modal-title').textContent = 'PowerShell Obfuscator';
}

function showPsObfListView() {
    document.getElementById('ps-obf-main-view').style.display = 'none';
    document.getElementById('ps-obf-list-view').style.display = '';
    document.getElementById('ps-obf-editor-view').style.display = 'none';
    document.getElementById('ps-obf-footer-main').style.display = 'none';
    document.getElementById('ps-obf-footer-list').style.display = '';
    document.getElementById('ps-obf-footer-editor').style.display = 'none';
    document.getElementById('ps-obf-modal-title').textContent = 'Manage Obfuscation Methods';
    loadPsObfMethodList();
}

function showPsObfEditorView() {
    document.getElementById('ps-obf-main-view').style.display = 'none';
    document.getElementById('ps-obf-list-view').style.display = 'none';
    document.getElementById('ps-obf-editor-view').style.display = '';
    document.getElementById('ps-obf-footer-main').style.display = 'none';
    document.getElementById('ps-obf-footer-list').style.display = 'none';
    document.getElementById('ps-obf-footer-editor').style.display = '';
}

async function loadPsObfMethodList() {
    const container = document.getElementById('ps-obf-method-list');
    container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">Loading...</div>';

    try {
        const resp = await fetch('/api/ps-obfuscation-methods');
        const data = await resp.json();

        if (!data.methods || data.methods.length === 0) {
            container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">No obfuscation methods configured. Click "+ New Method" to create one.</div>';
            return;
        }

        // Fetch raw data for each method to get command previews
        let html = '';
        for (const m of data.methods) {
            let preview = '';
            try {
                const rawResp = await fetch(`/api/ps-obfuscation-method/${encodeURIComponent(m.name)}/raw`);
                const rawData = await rawResp.json();
                preview = (rawData.command || '').trim().split('\n')[0];
                if (preview.length > 80) preview = preview.substring(0, 80) + '...';
            } catch (e) { /* ignore */ }

            html += `
                <div class="ps-obf-method-card">
                    <div class="ps-obf-method-card-info">
                        <div class="ps-obf-method-card-name">${escapeHtml(m.name)}</div>
                        <div class="ps-obf-method-card-preview">${escapeHtml(preview)}</div>
                    </div>
                    <div class="ps-obf-method-card-actions">
                        <button class="btn btn-secondary btn-sm" onclick="openPsObfEditor('edit', '${escapeHtml(m.name).replace(/'/g, "\\'")}')">Edit</button>
                        <button class="btn btn-danger btn-sm" onclick="deletePsObfMethod('${escapeHtml(m.name).replace(/'/g, "\\'")}')">Delete</button>
                    </div>
                </div>
            `;
        }
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<div style="color:var(--red);text-align:center;padding:2rem;">Error loading methods: ${escapeHtml(e.message)}</div>`;
    }
}

async function openPsObfEditor(mode, name) {
    psObfEditorMode = mode;
    psObfEditorOriginalName = mode === 'edit' ? name : '';
    document.getElementById('ps-obf-modal-title').textContent = mode === 'create' ? 'New Obfuscation Method' : 'Edit Obfuscation Method';

    // Clear fields
    document.getElementById('ps-obf-editor-name').value = '';
    document.getElementById('ps-obf-editor-command').value = '';

    if (mode === 'edit' && name) {
        try {
            const resp = await fetch(`/api/ps-obfuscation-method/${encodeURIComponent(name)}/raw`);
            const data = await resp.json();
            if (data.error) {
                showNotificationPopup(data.error, 'error');
                return;
            }
            document.getElementById('ps-obf-editor-name').value = data.name || '';
            document.getElementById('ps-obf-editor-command').value = data.command || '';
        } catch (e) {
            showNotificationPopup('Error loading method: ' + e.message, 'error');
            return;
        }
    }

    showPsObfEditorView();
}

async function savePsObfMethod() {
    const name = document.getElementById('ps-obf-editor-name').value.trim();
    const command = document.getElementById('ps-obf-editor-command').value.trim();

    if (!name) {
        showNotificationPopup('Method name is required', 'error');
        return;
    }
    if (!command) {
        showNotificationPopup('Method command is required', 'error');
        return;
    }

    const payload = { name, command };

    try {
        let resp;
        if (psObfEditorMode === 'create') {
            resp = await fetch('/api/ps-obfuscation-methods/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            resp = await fetch(`/api/ps-obfuscation-method/${encodeURIComponent(psObfEditorOriginalName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup(psObfEditorMode === 'create' ? 'Method created!' : 'Method updated!', 'success');
            showPsObfListView();
        } else {
            showNotificationPopup(result.error || 'Failed to save method', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error saving method: ' + e.message, 'error');
    }
}

async function deletePsObfMethod(name) {
    if (!confirm(`Delete obfuscation method "${name}"?`)) return;

    try {
        const resp = await fetch(`/api/ps-obfuscation-method/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup('Method deleted', 'success');
            loadPsObfMethodList();
        } else {
            showNotificationPopup(result.error || 'Failed to delete method', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error deleting method: ' + e.message, 'error');
    }
}

async function refreshPsObfDropdowns() {
    // Refresh the obfuscation level dropdown and cradle obfuscation dropdown
    try {
        const response = await fetch('/api/ps-obfuscation-methods');
        const data = await response.json();

        const levelSelect = document.getElementById('obfuscate-ps-level');
        if (levelSelect) {
            const currentValue = levelSelect.value;
            levelSelect.innerHTML = '<option value="">None - No obfuscation</option>' +
                data.methods.map(m =>
                    `<option value="${m.name}">${m.name}</option>`
                ).join('');
            // Try to restore previous selection
            if (currentValue) {
                const exists = Array.from(levelSelect.options).some(o => o.value === currentValue);
                if (exists) levelSelect.value = currentValue;
            }
        }

        const cradleObfSelect = document.getElementById('obfuscate-ps-cradle-obf-method');
        if (cradleObfSelect) {
            const currentCradleValue = cradleObfSelect.value;
            cradleObfSelect.innerHTML = '<option value="">None</option>' +
                data.methods.map(m =>
                    `<option value="${m.name}">${m.name}</option>`
                ).join('');
            if (currentCradleValue) {
                const exists = Array.from(cradleObfSelect.options).some(o => o.value === currentCradleValue);
                if (exists) cradleObfSelect.value = currentCradleValue;
            }
        }
    } catch (error) {
        console.error('Failed to refresh obfuscation method dropdowns:', error);
    }
}

// ===== PS FEATURES MANAGER =====

let psFeatEditorMode = 'create';
let psFeatEditorOriginalName = '';

const PS_FEAT_TYPE_LABELS = {
    'amsi': 'AMSI Bypasses',
    'cradle-ps1': 'PS1 Download Cradles',
    'cradle-exe': 'EXE Download Cradles',
    'cradle-dll': 'DLL Download Cradles'
};

function showPsFeatManager() {
    const modal = document.getElementById('ps-features-modal');
    document.getElementById('ps-feat-modal-title').textContent = 'PS Features Manager';
    showPsFeatListView();
    modal.classList.add('active');
    loadPsFeatList();
}

function showPsFeatListView() {
    document.getElementById('ps-feat-list-view').style.display = '';
    document.getElementById('ps-feat-editor-view').style.display = 'none';
    document.getElementById('ps-feat-generate-view').style.display = 'none';
    document.getElementById('ps-feat-modal-title').textContent = 'PS Features Manager';
}

function showPsFeatEditorView() {
    document.getElementById('ps-feat-list-view').style.display = 'none';
    document.getElementById('ps-feat-editor-view').style.display = '';
    document.getElementById('ps-feat-generate-view').style.display = 'none';
}

function showPsFeatGenerateView() {
    document.getElementById('ps-feat-list-view').style.display = 'none';
    document.getElementById('ps-feat-editor-view').style.display = 'none';
    document.getElementById('ps-feat-generate-view').style.display = '';
}

async function loadPsFeatList() {
    const container = document.getElementById('ps-feat-list');
    container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">Loading...</div>';

    try {
        const resp = await fetch('/api/ps-features');
        const data = await resp.json();

        if (!data.features) {
            container.innerHTML = '<div style="color:var(--red);text-align:center;padding:2rem;">Error loading features</div>';
            return;
        }

        const typeOrder = ['amsi', 'cradle-ps1', 'cradle-exe', 'cradle-dll'];
        let html = '';
        let totalCount = 0;

        for (const ftype of typeOrder) {
            const items = data.features[ftype] || [];
            if (items.length === 0) continue;
            totalCount += items.length;

            html += `<div class="ps-feat-type-group">`;
            html += `<div class="ps-feat-type-header">${PS_FEAT_TYPE_LABELS[ftype] || ftype} (${items.length})</div>`;

            for (const item of items) {
                const tags = [];
                if (item.has_code) tags.push('code');
                if (item.has_command) tags.push('command');
                const noObfTag = item.no_obf ? '<span class="ps-feat-tag ps-feat-tag-noobf">no-obf</span>' : '';

                html += `
                    <div class="ps-feat-card">
                        <div class="ps-feat-card-info">
                            <div class="ps-feat-card-name">${escapeHtml(item.name)}</div>
                            <div class="ps-feat-card-meta">
                                ${tags.map(t => `<span class="ps-feat-tag">${t}</span>`).join('')}
                                ${noObfTag}
                            </div>
                        </div>
                        <div class="ps-feat-card-actions">
                            <button class="btn btn-primary btn-sm" onclick="openPsFeatGenerate('${escapeHtml(item.name).replace(/'/g, "\\'")}')">View</button>
                            <button class="btn btn-secondary btn-sm" onclick="openPsFeatEditor('edit', '${escapeHtml(item.name).replace(/'/g, "\\'")}')">Edit</button>
                            <button class="btn btn-danger btn-sm" onclick="deletePsFeat('${escapeHtml(item.name).replace(/'/g, "\\'")}')">Delete</button>
                        </div>
                    </div>
                `;
            }
            html += `</div>`;
        }

        if (totalCount === 0) {
            container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:2rem;">No PS features configured. Click "+ New Feature" to create one.</div>';
        } else {
            container.innerHTML = html;
        }
    } catch (e) {
        container.innerHTML = `<div style="color:var(--red);text-align:center;padding:2rem;">Error loading features: ${escapeHtml(e.message)}</div>`;
    }
}

async function openPsFeatEditor(mode, name) {
    psFeatEditorMode = mode;
    psFeatEditorOriginalName = mode === 'edit' ? name : '';
    document.getElementById('ps-feat-modal-title').textContent = mode === 'create' ? 'New PS Feature' : 'Edit PS Feature';

    // Clear fields
    document.getElementById('ps-feat-editor-name').value = '';
    document.getElementById('ps-feat-editor-type').value = 'amsi';
    document.getElementById('ps-feat-editor-no-obf').checked = false;
    document.getElementById('ps-feat-editor-code').value = '';
    document.getElementById('ps-feat-editor-command').value = '';

    if (mode === 'edit' && name) {
        try {
            const resp = await fetch(`/api/ps-feature/${encodeURIComponent(name)}/raw`);
            const data = await resp.json();
            if (data.error) {
                showNotificationPopup(data.error, 'error');
                return;
            }
            document.getElementById('ps-feat-editor-name').value = data.name || '';
            document.getElementById('ps-feat-editor-type').value = data.type || 'amsi';
            document.getElementById('ps-feat-editor-no-obf').checked = data['no-obf'] || false;
            document.getElementById('ps-feat-editor-code').value = data.code || '';
            document.getElementById('ps-feat-editor-command').value = data.command || '';
        } catch (e) {
            showNotificationPopup('Error loading feature: ' + e.message, 'error');
            return;
        }
    }

    showPsFeatEditorView();
}

async function savePsFeat() {
    const name = document.getElementById('ps-feat-editor-name').value.trim();
    const type = document.getElementById('ps-feat-editor-type').value;
    const noObf = document.getElementById('ps-feat-editor-no-obf').checked;
    const code = document.getElementById('ps-feat-editor-code').value.trim();
    const command = document.getElementById('ps-feat-editor-command').value.trim();

    if (!name) {
        showNotificationPopup('Feature name is required', 'error');
        return;
    }
    if (!code && !command) {
        showNotificationPopup('Either code or command is required', 'error');
        return;
    }

    const payload = { name, type, no_obf: noObf };
    if (code) payload.code = code;
    if (command) payload.command = command;

    try {
        let resp;
        if (psFeatEditorMode === 'create') {
            resp = await fetch('/api/ps-features/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            resp = await fetch(`/api/ps-feature/${encodeURIComponent(psFeatEditorOriginalName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup(psFeatEditorMode === 'create' ? 'Feature created!' : 'Feature updated!', 'success');
            showPsFeatListView();
            loadPsFeatList();
        } else {
            showNotificationPopup(result.error || 'Failed to save feature', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error saving feature: ' + e.message, 'error');
    }
}

async function deletePsFeat(name) {
    if (!confirm(`Delete PS feature "${name}"?`)) return;

    try {
        const resp = await fetch(`/api/ps-feature/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        const result = await resp.json();
        if (resp.ok && result.success) {
            showNotificationPopup('Feature deleted', 'success');
            loadPsFeatList();
        } else {
            showNotificationPopup(result.error || 'Failed to delete feature', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error deleting feature: ' + e.message, 'error');
    }
}

// PS Features generate functions

async function openPsFeatGenerate(name) {
    document.getElementById('ps-feat-modal-title').textContent = `View: ${name}`;
    document.getElementById('ps-feat-generate-result').style.display = 'none';
    document.getElementById('ps-feat-generate-btn').dataset.featureName = name;
    document.getElementById('ps-feat-generate-btn').disabled = false;
    document.getElementById('ps-feat-generate-save-status').style.display = 'none';

    const container = document.getElementById('ps-feat-generate-params-container');
    container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:1rem;">Loading...</div>';

    showPsFeatGenerateView();

    try {
        const resp = await fetch(`/api/ps-feature/${encodeURIComponent(name)}/info`);
        const info = await resp.json();

        if (info.error) {
            container.innerHTML = `<div style="color:var(--red);">${escapeHtml(info.error)}</div>`;
            return;
        }

        const hasParams = info.parameters && info.parameters.length > 0;
        const hasCommand = info.has_command;

        if (!hasParams && !hasCommand) {
            // No parameters, no command to run — static code, generate immediately
            container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:1rem;">Generating...</div>';
            document.getElementById('ps-feat-generate-btn').style.display = 'none';
            await generatePsFeat();
            container.innerHTML = '';
            return;
        }

        if (!hasParams && hasCommand) {
            // Command-based but no user parameters needed — still generate immediately
            container.innerHTML = '<div style="color:var(--subtext0);text-align:center;padding:1rem;">Generating...</div>';
            document.getElementById('ps-feat-generate-btn').style.display = 'none';
            await generatePsFeat();
            container.innerHTML = '';
            return;
        }

        // Has parameters — show the form
        document.getElementById('ps-feat-generate-btn').style.display = '';
        let html = '';
        info.parameters.forEach(param => {
            let defaultVal = param.default || '';
            // Auto-fill lhost from global settings
            if (param.name === 'lhost') {
                const settingsLhost = getDefaultLhost();
                if (settingsLhost) defaultVal = settingsLhost;
            }
            // Auto-fill output_path from global settings
            if (param.name === 'output_path') {
                const settingsOutputDir = getDefaultOutputDir();
                if (settingsOutputDir) defaultVal = settingsOutputDir;
            }

            const isRequired = param.required || false;
            html += `
                <div class="param-form-item">
                    <label class="param-form-label">
                        ${escapeHtml(param.label || param.name)}
                        ${isRequired ? '<span class="param-required">*</span>' : ''}
                        <span class="param-type">[${escapeHtml(param.type)}]</span>
                    </label>
                    <input type="text"
                           class="param-form-input"
                           data-ps-feat-param="${escapeHtml(param.name)}"
                           data-required="${isRequired}"
                           value="${escapeHtml(String(defaultVal))}"
                           placeholder="${escapeHtml(param.description || '')}">
                    <div class="param-form-description">${escapeHtml(param.description || '')}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<div style="color:var(--red);">Error: ${escapeHtml(e.message)}</div>`;
    }
}

async function generatePsFeat() {
    const name = document.getElementById('ps-feat-generate-btn').dataset.featureName;
    const generateBtn = document.getElementById('ps-feat-generate-btn');
    generateBtn.disabled = true;
    const origText = generateBtn.textContent;
    generateBtn.textContent = 'Generating...';

    // Collect parameters
    const parameters = {};
    document.querySelectorAll('#ps-feat-generate-params-container [data-ps-feat-param]').forEach(input => {
        parameters[input.dataset.psFeatParam] = input.value.trim();
    });

    try {
        const resp = await fetch('/api/ps-features/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parameters })
        });

        const result = await resp.json();

        if (resp.ok && result.success) {
            document.getElementById('ps-feat-generate-result').style.display = '';
            document.getElementById('ps-feat-generate-output').value = result.output;
            document.getElementById('ps-feat-generate-save-status').style.display = 'none';

            // Set default filename based on feature type
            const ext = result.feature_type === 'amsi' ? 'ps1' : 'ps1';
            document.getElementById('ps-feat-generate-save-filename').value = `${name.replace(/[^a-zA-Z0-9_-]/g, '_')}.${ext}`;
        } else {
            showNotificationPopup(result.error || 'Generation failed', 'error');
        }
    } catch (e) {
        showNotificationPopup('Error generating feature: ' + e.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = origText;
    }
}

async function savePsFeatOutput() {
    const content = document.getElementById('ps-feat-generate-output').value;
    const filenameInput = document.getElementById('ps-feat-generate-save-filename');
    const saveBtn = document.getElementById('ps-feat-generate-save-btn');
    const statusDiv = document.getElementById('ps-feat-generate-save-status');

    let filename = filenameInput.value.trim();
    if (!filename) {
        showNotificationPopup('Please enter a filename', 'error');
        filenameInput.focus();
        return;
    }
    if (!content) {
        showNotificationPopup('No content to save', 'error');
        return;
    }

    saveBtn.disabled = true;
    statusDiv.style.display = 'none';

    try {
        const resp = await fetch('/api/ps-features/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, filename })
        });

        const result = await resp.json();

        if (resp.ok && result.success) {
            statusDiv.textContent = `Saved to: ${result.path}`;
            statusDiv.style.display = 'block';
            statusDiv.style.borderColor = 'var(--teal)';
            statusDiv.style.color = 'var(--teal)';
        } else {
            statusDiv.textContent = `Error: ${result.error}`;
            statusDiv.style.display = 'block';
            statusDiv.style.borderColor = 'var(--red)';
            statusDiv.style.color = 'var(--red)';
        }
    } catch (e) {
        statusDiv.textContent = `Error: ${e.message}`;
        statusDiv.style.display = 'block';
        statusDiv.style.borderColor = 'var(--red)';
        statusDiv.style.color = 'var(--red)';
    } finally {
        saveBtn.disabled = false;
    }
}

// ===== EDITOR & VERSION EVENT WIRING =====

document.addEventListener('DOMContentLoaded', function() {
    // Create recipe button
    const createBtn = document.getElementById('create-recipe-btn');
    if (createBtn) createBtn.addEventListener('click', () => openEditor('create', null));

    // Recipe header action buttons (Edit, Versions, Delete)
    const editBtn = document.getElementById('edit-recipe-btn');
    if (editBtn) editBtn.addEventListener('click', openEditorForEdit);
    const versionsBtn = document.getElementById('versions-recipe-btn');
    if (versionsBtn) versionsBtn.addEventListener('click', openVersionHistory);
    const deleteBtn = document.getElementById('delete-recipe-btn');
    if (deleteBtn) deleteBtn.addEventListener('click', deleteCurrentRecipe);

    // Editor tab switching
    document.querySelectorAll('.editor-tab').forEach(tab => {
        tab.addEventListener('click', () => switchEditorTab(tab.dataset.tab));
    });

    // Output type toggle
    const outputType = document.getElementById('editor-output-type');
    if (outputType) outputType.addEventListener('change', toggleOutputFields);

    // Compile toggle
    const compileEnabled = document.getElementById('editor-compile-enabled');
    if (compileEnabled) compileEnabled.addEventListener('change', toggleCompileFields);

    // Add artifact
    const addArtifact = document.getElementById('editor-add-artifact');
    if (addArtifact) addArtifact.addEventListener('click', () => addArtifactRow(''));

    // Add parameter
    const addParam = document.getElementById('editor-add-param');
    if (addParam) addParam.addEventListener('click', () => addParamRow(null));

    // Add preprocessing
    const addPreproc = document.getElementById('editor-add-preproc');
    if (addPreproc) addPreproc.addEventListener('click', () => addPreprocRow(null));

    // Category combobox
    initCategoryCombobox();

    // Save/Validate/Cancel
    const saveBtn = document.getElementById('editor-save-btn');
    if (saveBtn) saveBtn.addEventListener('click', saveRecipe);

    const cancelBtn = document.getElementById('editor-cancel-btn');
    if (cancelBtn) cancelBtn.addEventListener('click', () => closeModal('recipe-editor-modal'));

    // Version history
    const useBtn = document.getElementById('version-use-btn');
    if (useBtn) useBtn.addEventListener('click', useVersion);

    const removeLatestBtn = document.getElementById('version-remove-latest-btn');
    if (removeLatestBtn) removeLatestBtn.addEventListener('click', removeLatestVersion);

    const versionCloseBtn = document.getElementById('version-close-btn');
    if (versionCloseBtn) versionCloseBtn.addEventListener('click', () => closeModal('version-history-modal'));

    // Shellcode manager
    const scMgrBtn = document.getElementById('shellcode-mgr-btn');
    if (scMgrBtn) scMgrBtn.addEventListener('click', showShellcodeManager);

    const scCreateBtn = document.getElementById('shellcode-mgr-create-btn');
    if (scCreateBtn) scCreateBtn.addEventListener('click', () => openScEditor('create'));

    const scEditorSaveBtn = document.getElementById('sc-editor-save-btn');
    if (scEditorSaveBtn) scEditorSaveBtn.addEventListener('click', saveShellcode);

    const scEditorCancelBtn = document.getElementById('sc-editor-cancel-btn');
    if (scEditorCancelBtn) scEditorCancelBtn.addEventListener('click', () => { showScListView(); loadShellcodeList(); });

    const scAddParamBtn = document.getElementById('sc-editor-add-param');
    if (scAddParamBtn) scAddParamBtn.addEventListener('click', () => addScParamRow(null));

    const scGenerateBtn = document.getElementById('sc-generate-btn');
    if (scGenerateBtn) scGenerateBtn.addEventListener('click', generateShellcode);

    const scGenerateBackBtn = document.getElementById('sc-generate-back-btn');
    if (scGenerateBackBtn) scGenerateBackBtn.addEventListener('click', () => { showScListView(); });

    const scCopyHexBtn = document.getElementById('sc-generate-copy-hex');
    if (scCopyHexBtn) scCopyHexBtn.addEventListener('click', () => {
        const hex = document.getElementById('sc-generate-output-hex').value;
        navigator.clipboard.writeText(hex).then(() => {
            showNotificationPopup('Shellcode copied!', 'success');
        });
    });

    const scCopyListenerBtn = document.getElementById('sc-generate-copy-listener');
    if (scCopyListenerBtn) scCopyListenerBtn.addEventListener('click', () => {
        const cmd = document.getElementById('sc-generate-listener-cmd').value;
        navigator.clipboard.writeText(cmd).then(() => {
            showNotificationPopup('Listener command copied!', 'success');
        });
    });

    const scSaveBtn = document.getElementById('sc-generate-save-btn');
    if (scSaveBtn) scSaveBtn.addEventListener('click', saveGeneratedShellcode);

    // PS obfuscation method manager
    const psObfManageBtn = document.getElementById('ps-obf-manage-btn');
    if (psObfManageBtn) psObfManageBtn.addEventListener('click', showPsObfListView);

    const psObfCreateBtn = document.getElementById('ps-obf-create-btn');
    if (psObfCreateBtn) psObfCreateBtn.addEventListener('click', () => openPsObfEditor('create'));

    const psObfListBackBtn = document.getElementById('ps-obf-list-back-btn');
    if (psObfListBackBtn) psObfListBackBtn.addEventListener('click', () => {
        showPsObfMainView();
        // Refresh the method dropdown when coming back from management
        refreshPsObfDropdowns();
    });

    const psObfEditorSaveBtn = document.getElementById('ps-obf-editor-save-btn');
    if (psObfEditorSaveBtn) psObfEditorSaveBtn.addEventListener('click', savePsObfMethod);

    const psObfEditorCancelBtn = document.getElementById('ps-obf-editor-cancel-btn');
    if (psObfEditorCancelBtn) psObfEditorCancelBtn.addEventListener('click', showPsObfListView);

    // PS features manager
    const psFeatBtn = document.getElementById('ps-features-btn');
    if (psFeatBtn) psFeatBtn.addEventListener('click', showPsFeatManager);

    const psFeatCreateBtn = document.getElementById('ps-feat-create-btn');
    if (psFeatCreateBtn) psFeatCreateBtn.addEventListener('click', () => openPsFeatEditor('create'));

    const psFeatEditorSaveBtn = document.getElementById('ps-feat-editor-save-btn');
    if (psFeatEditorSaveBtn) psFeatEditorSaveBtn.addEventListener('click', savePsFeat);

    const psFeatEditorCancelBtn = document.getElementById('ps-feat-editor-cancel-btn');
    if (psFeatEditorCancelBtn) psFeatEditorCancelBtn.addEventListener('click', () => { showPsFeatListView(); loadPsFeatList(); });

    const psFeatGenerateBtn = document.getElementById('ps-feat-generate-btn');
    if (psFeatGenerateBtn) psFeatGenerateBtn.addEventListener('click', generatePsFeat);

    const psFeatGenerateBackBtn = document.getElementById('ps-feat-generate-back-btn');
    if (psFeatGenerateBackBtn) psFeatGenerateBackBtn.addEventListener('click', () => { showPsFeatListView(); });

    const psFeatCopyBtn = document.getElementById('ps-feat-generate-copy');
    if (psFeatCopyBtn) psFeatCopyBtn.addEventListener('click', () => {
        const output = document.getElementById('ps-feat-generate-output').value;
        navigator.clipboard.writeText(output).then(() => {
            showNotificationPopup('Copied to clipboard!', 'success');
        });
    });

    const psFeatSaveBtn = document.getElementById('ps-feat-generate-save-btn');
    if (psFeatSaveBtn) psFeatSaveBtn.addEventListener('click', savePsFeatOutput);

    // Modal close buttons for new modals
    document.querySelectorAll('#recipe-editor-modal .modal-close, #version-history-modal .modal-close, #shellcode-mgr-modal .modal-close, #ps-features-modal .modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').classList.remove('active');
        });
    });
});
