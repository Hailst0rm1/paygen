// Paygen Web GUI - Main JavaScript

// Global state
let recipes = {};
let selectedRecipe = null;
let categories = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadRecipes();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Header buttons
    document.getElementById('history-btn').addEventListener('click', showHistory);
    document.getElementById('refresh-btn').addEventListener('click', loadRecipes);
    
    // Fullscreen toggle for code preview
    const fullscreenToggle = document.getElementById('fullscreen-toggle');
    const codePreviewPanel = document.getElementById('code-preview-panel');
    const fullscreenIcon = document.getElementById('fullscreen-icon');
    
    if (fullscreenToggle && codePreviewPanel && fullscreenIcon) {
        fullscreenToggle.addEventListener('click', () => {
            codePreviewPanel.classList.toggle('fullscreen');
        });
        
        // Keyboard shortcut for fullscreen (Ctrl+F)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                codePreviewPanel.classList.toggle('fullscreen');
            }
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
async function loadRecipes() {
    try {
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
    } catch (error) {
        console.error('Failed to load recipes:', error);
        document.getElementById('categories-panel').innerHTML = 
            '<div class="loading">Failed to load recipes. Please refresh.</div>';
    }
}

// Render categories and recipes
function renderCategories(filterQuery = '') {
    const container = document.getElementById('categories-container');
    if (!container) return;
    
    let html = '';
    
    // Filter recipes if query provided
    let filteredCategories = categories;
    if (filterQuery) {
        const queryLower = filterQuery.toLowerCase();
        filteredCategories = {};
        
        Object.keys(categories).forEach(categoryName => {
            const matchingRecipes = categories[categoryName].filter(recipe => 
                recipe.name.toLowerCase().includes(queryLower)
            );
            if (matchingRecipes.length > 0) {
                filteredCategories[categoryName] = matchingRecipes;
            }
        });
    }
    
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
    html += `<div class="recipe-category">Category: ${escapeHtml(recipe.category)}</div>`;
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
        `<div class="description-line">${escapeHtml(line)}</div>`
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
function showParameterForm() {
    if (!selectedRecipe) return;
    
    const container = document.getElementById('param-form-container');
    let html = '';
    
    if (selectedRecipe.parameters && selectedRecipe.parameters.length > 0) {
        selectedRecipe.parameters.forEach(param => {
            html += `
                <div class="param-form-item">
                    <label class="param-form-label">
                        ${param.name}
                        ${param.required ? '<span class="param-required">*</span>' : ''}
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
        html = '<p>This recipe has no configurable parameters.</p>';
    }
    
    // Add build options section
    html += `
        <div class="param-form-separator"></div>
        <div class="param-form-section-title">Build Options</div>
    `;
    
    // Only show "remove comments" option for template-based recipes
    const outputType = selectedRecipe.output?.type || 'template';
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
                <input type="checkbox" id="build-strip-binaries" class="param-form-checkbox" checked>
                Strip binary metadata
            </label>
            <div class="param-form-description">Remove debug symbols and metadata from compiled binaries</div>
        </div>
    `;
    
    container.innerHTML = html;
    
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
    
    // Initial validation of all fields
    validateAllParameters();
    
    document.getElementById('param-modal').classList.add('active');
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
        if (!validateParameter(input)) {
            allValid = false;
        }
    });
    
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
    
    // Store parameters globally for launch instruction substitution
    window.currentBuildParameters = parameters;
    
    // Collect build options
    const buildOptions = {
        remove_comments: document.getElementById('build-remove-comments')?.checked || false,
        remove_console_output: document.getElementById('build-remove-console')?.checked || false,
        strip_binaries: document.getElementById('build-strip-binaries')?.checked || false
    };
    
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
                                // Truncate output to 500 chars like TUI
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
                            // Truncate output to 500 chars like TUI
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
                
                closeBtn.style.display = 'block';
            } else if (data.status === 'failed') {
                clearInterval(interval);
                resultContainer.innerHTML = `
                    <div style="background: var(--surface0); padding: 1rem; border-radius: 4px; border-left: 3px solid var(--red);">
                        <div style="color: var(--red); font-weight: bold;">❌ Build failed</div>
                        ${data.error ? `<div style="color: var(--text); margin-top: 0.5rem;">${escapeHtml(data.error)}</div>` : ''}
                    </div>
                `;
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
                                ${step.error ? `<div class="history-detail-step-error">${escapeHtml(step.error.substring(0, 200))}</div>` : ''}
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
            
            // Store old ID, change to expected ID, render, restore
            const oldId = launchContainer.id;
            launchContainer.id = 'launch-instructions-md';
            renderLaunchInstructions(instructions);
            launchContainer.id = oldId;
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
