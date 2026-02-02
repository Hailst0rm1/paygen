// Paygen Web GUI - Main JavaScript

// Global state
let recipes = {};
let selectedRecipe = null;
let categories = {};
let activeEffectivenessFilters = new Set();

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
    document.getElementById('refresh-btn').addEventListener('click', () => loadRecipes(true));
    
    // Effectiveness filter pills
    document.querySelectorAll('.filter-pill').forEach(pill => {
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
            this.closest('.modal').classList.remove('active');
        });
    });
    
    // Parameter modal buttons
    document.getElementById('cancel-generate-btn').addEventListener('click', function() {
        document.getElementById('param-modal').classList.remove('active');
    });
    
    document.getElementById('confirm-generate-btn').addEventListener('click', generatePayload);
    
    // Build modal close button
    document.getElementById('close-build-btn').addEventListener('click', function() {
        document.getElementById('build-modal').classList.remove('active');
    });
    
    // History modal buttons
    document.getElementById('close-history-btn').addEventListener('click', function() {
        document.getElementById('history-modal').classList.remove('active');
    });
    
    // Clear history button handler is set dynamically in showHistory/showHistoryDetail
    // Don't add a static event listener here
    
    // PowerShell Obfuscator modal buttons
    document.getElementById('close-obfuscate-ps-btn').addEventListener('click', function() {
        document.getElementById('obfuscate-ps-modal').classList.remove('active');
    });
    
    document.getElementById('obfuscate-ps-generate-btn').addEventListener('click', generateObfuscatedPs);
    
    document.getElementById('obfuscate-ps-copy-btn').addEventListener('click', copyObfuscatedPs);
    
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
            const matchesSearch = !filterQuery || recipe.name.toLowerCase().includes(filterQuery.toLowerCase());
            
            // Check if recipe matches effectiveness filter
            // If no filters are active, show all recipes
            const matchesEffectiveness = activeEffectivenessFilters.size === 0 || 
                                        activeEffectivenessFilters.has(recipe.effectiveness.toLowerCase());
            
            return matchesSearch && matchesEffectiveness;
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
            let preprocessorType = step.script ? 'script' : (step.command ? 'command' : 'unknown');
            
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
    html += `
        <button class="btn btn-generate" onclick="showParameterForm()">
            <span class="btn-icon">🚀</span> Generate Payload
        </button>
    `;
    
    panel.innerHTML = html;
    
    // Render Markdown for launch instructions
    if (recipe.launch_instructions) {
        renderLaunchInstructions(recipe.launch_instructions);
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
                const defaultVal = param.default !== undefined ? param.default : '';
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
        const isPS1 = templatePath.toLowerCase().endsWith('.ps1');
        const isCS = templatePath.toLowerCase().endsWith('.cs');
        
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
                        if (lhostContainer) lhostContainer.style.display = checked ? 'block' : 'none';
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
                        if (lhostContainer) lhostContainer.style.display = checked ? 'block' : 'none';
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
    
    // Find parameter definition
    const param = selectedRecipe.parameters.find(p => p.name === paramName);
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
                build_options: buildOptions
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
        const stats = data.stats || {total: 0, success: 0, failed: 0};
        document.getElementById('history-stats').textContent = 
            `Total: ${stats.total} | Success: ${stats.success} | Failed: ${stats.failed}`;
        
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
        
        // Store entries for detail view
        window.historyEntries = data.entries;
        
        // Reset footer buttons to list mode
        const clearBtn = document.getElementById('clear-history-btn');
        const backBtn = document.getElementById('back-history-btn');
        if (clearBtn) {
            clearBtn.textContent = 'Clear All';
            clearBtn.onclick = clearHistory;
        }
        if (backBtn) {
            backBtn.style.display = 'none';
        }
        
        document.getElementById('history-modal').classList.add('active');
        
    } catch (error) {
        console.error('Failed to load history:', error);
        alert('Failed to load build history');
    }
}

// Show detailed view of a history entry
function showHistoryDetail(index) {
    const entry = window.historyEntries[index];
    if (!entry) return;
    
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
        };
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

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== PowerShell Obfuscator Functions =====

// Show PowerShell Obfuscator modal
async function showObfuscatePsModal() {
    const modal = document.getElementById('obfuscate-ps-modal');
    const inputTextarea = document.getElementById('obfuscate-ps-input');
    const outputSection = document.getElementById('obfuscate-ps-output-section');
    const loadingDiv = document.getElementById('obfuscate-ps-loading');
    const levelSelect = document.getElementById('obfuscate-ps-level');
    
    // Reset modal state
    inputTextarea.value = '';
    outputSection.style.display = 'none';
    loadingDiv.style.display = 'none';
    
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
    
    // Show modal
    modal.classList.add('active');
    
    // Focus on input
    setTimeout(() => inputTextarea.focus(), 100);
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
        
        // Apply syntax highlighting
        Prism.highlightAllUnder(outputDiv);
        
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
