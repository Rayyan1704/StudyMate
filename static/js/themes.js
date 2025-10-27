// StudyMate AI - Theme Management

let currentTheme = 'light';
const availableThemes = ['light', 'dark', 'blue', 'green', 'purple', 'rose', 'orange'];

// Initialize theme system
function initializeThemes() {
    // Load saved theme
    const savedTheme = localStorage.getItem('studymate-theme') || 'light';
    setTheme(savedTheme);
    
    // Setup theme selector if it exists
    setupThemeSelector();
    
    // Listen for system theme changes
    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', handleSystemThemeChange);
    }
    
    console.log(`🎨 Theme system initialized with ${savedTheme} theme`);
}

// Set theme
function setTheme(themeName) {
    if (!availableThemes.includes(themeName)) {
        console.warn(`Theme ${themeName} not found, using light theme`);
        themeName = 'light';
    }
    
    currentTheme = themeName;
    document.documentElement.setAttribute('data-theme', themeName);
    
    // Update theme selector
    updateThemeSelector();
    
    // Save preference
    localStorage.setItem('studymate-theme', themeName);
    
    // Update meta theme-color for mobile browsers
    updateMetaThemeColor();
    
    console.log(`🎨 Theme changed to ${themeName}`);
}

// Toggle between light and dark theme
function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

// Cycle through all themes
function cycleTheme() {
    const currentIndex = availableThemes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % availableThemes.length;
    setTheme(availableThemes[nextIndex]);
}

// Setup theme selector
function setupThemeSelector() {
    const themeSelector = document.getElementById('themeSelector');
    if (!themeSelector) return;
    
    themeSelector.innerHTML = availableThemes.map(theme => `
        <div class=\"theme-option\" data-theme=\"${theme}\" onclick=\"setTheme('${theme}')\">
            <div class=\"theme-preview\"></div>
            <div class=\"theme-name\">${capitalizeFirst(theme)}</div>
        </div>
    `).join('');
    
    updateThemeSelector();
}

// Update theme selector active state
function updateThemeSelector() {
    document.querySelectorAll('.theme-option').forEach(option => {
        option.classList.toggle('active', option.dataset.theme === currentTheme);
    });
    
    // Update theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// Handle system theme change
function handleSystemThemeChange(e) {
    const autoTheme = localStorage.getItem('studymate-auto-theme');
    if (autoTheme === 'true') {
        setTheme(e.matches ? 'dark' : 'light');
    }
}

// Enable/disable auto theme
function toggleAutoTheme() {
    const autoTheme = localStorage.getItem('studymate-auto-theme') !== 'true';
    localStorage.setItem('studymate-auto-theme', autoTheme);
    
    if (autoTheme) {
        // Follow system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
    
    updateAutoThemeToggle();
}

// Update auto theme toggle
function updateAutoThemeToggle() {
    const autoThemeToggle = document.getElementById('autoThemeToggle');
    if (autoThemeToggle) {
        const isAuto = localStorage.getItem('studymate-auto-theme') === 'true';
        autoThemeToggle.classList.toggle('active', isAuto);
    }
}

// Update meta theme color for mobile browsers
function updateMetaThemeColor() {
    let themeColor = '#ffffff'; // Default light theme
    
    const themeColors = {
        light: '#ffffff',
        dark: '#0f172a',
        blue: '#f0f9ff',
        green: '#f0fdf4',
        purple: '#faf5ff',
        rose: '#fff1f2',
        orange: '#fff7ed'
    };
    
    themeColor = themeColors[currentTheme] || themeColors.light;
    
    // Update or create meta theme-color tag
    let metaThemeColor = document.querySelector('meta[name=\"theme-color\"]');
    if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.name = 'theme-color';
        document.head.appendChild(metaThemeColor);
    }
    metaThemeColor.content = themeColor;
}

// Get theme colors for JavaScript use
function getThemeColors() {
    const computedStyle = getComputedStyle(document.documentElement);
    
    return {
        primary: computedStyle.getPropertyValue('--primary-color').trim(),
        secondary: computedStyle.getPropertyValue('--secondary-color').trim(),
        accent: computedStyle.getPropertyValue('--accent-color').trim(),
        background: computedStyle.getPropertyValue('--bg-primary').trim(),
        text: computedStyle.getPropertyValue('--text-primary').trim(),
        border: computedStyle.getPropertyValue('--border-color').trim()
    };
}

// Apply theme to dynamic elements
function applyThemeToElement(element, customColors = {}) {
    const colors = { ...getThemeColors(), ...customColors };
    
    Object.entries(colors).forEach(([property, value]) => {
        element.style.setProperty(`--${property}`, value);
    });
}

// Theme animation effects
function animateThemeChange() {
    document.body.classList.add('theme-transition');
    
    setTimeout(() => {
        document.body.classList.remove('theme-transition');
    }, 300);
}

// Custom theme creation
function createCustomTheme(name, colors) {
    const style = document.createElement('style');
    style.id = `custom-theme-${name}`;
    
    const cssVars = Object.entries(colors)
        .map(([key, value]) => `--${key}: ${value};`)
        .join('\\n    ');
    
    style.textContent = `
        [data-theme=\"${name}\"] {
            ${cssVars}
        }
    `;
    
    document.head.appendChild(style);
    
    // Add to available themes
    if (!availableThemes.includes(name)) {
        availableThemes.push(name);
        setupThemeSelector();
    }
}

// Export theme settings
function exportThemeSettings() {
    const settings = {
        currentTheme,
        autoTheme: localStorage.getItem('studymate-auto-theme') === 'true',
        customThemes: getCustomThemes()
    };
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'studymate-theme-settings.json';
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Import theme settings
function importThemeSettings(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const settings = JSON.parse(e.target.result);
            
            // Apply imported settings
            if (settings.currentTheme) {
                setTheme(settings.currentTheme);
            }
            
            if (settings.autoTheme !== undefined) {
                localStorage.setItem('studymate-auto-theme', settings.autoTheme);
                updateAutoThemeToggle();
            }
            
            // Import custom themes
            if (settings.customThemes) {
                settings.customThemes.forEach(theme => {
                    createCustomTheme(theme.name, theme.colors);
                });
            }
            
            showNotification('Theme settings imported successfully', 'success');
        } catch (error) {
            console.error('Error importing theme settings:', error);
            showNotification('Failed to import theme settings', 'error');
        }
    };
    reader.readAsText(file);
}

// Get custom themes
function getCustomThemes() {
    const customStyles = document.querySelectorAll('style[id^=\"custom-theme-\"]');
    return Array.from(customStyles).map(style => {
        const name = style.id.replace('custom-theme-', '');
        // Parse CSS to extract colors (simplified)
        const colors = {};
        const matches = style.textContent.match(/--([^:]+):\\s*([^;]+);/g);
        if (matches) {
            matches.forEach(match => {
                const [, key, value] = match.match(/--([^:]+):\\s*([^;]+);/);
                colors[key] = value.trim();
            });
        }
        return { name, colors };
    });
}

// Theme accessibility features
function enhanceThemeAccessibility() {
    // High contrast mode detection
    if (window.matchMedia) {
        const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
        highContrastQuery.addEventListener('change', (e) => {
            document.documentElement.classList.toggle('high-contrast', e.matches);
        });
        
        // Initial check
        document.documentElement.classList.toggle('high-contrast', highContrastQuery.matches);
    }
    
    // Reduced motion detection
    if (window.matchMedia) {
        const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        reducedMotionQuery.addEventListener('change', (e) => {
            document.documentElement.classList.toggle('reduced-motion', e.matches);
        });
        
        // Initial check
        document.documentElement.classList.toggle('reduced-motion', reducedMotionQuery.matches);
    }
}

// Theme keyboard shortcuts
function setupThemeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Shift + T for theme toggle
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggleTheme();
        }
        
        // Ctrl/Cmd + Shift + C for theme cycle
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            cycleTheme();
        }
    });
}

// Utility function
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Initialize theme system on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeThemes();
    enhanceThemeAccessibility();
    setupThemeKeyboardShortcuts();
    updateAutoThemeToggle();
});

// Export theme functions for global access
window.ThemeManager = {
    setTheme,
    toggleTheme,
    cycleTheme,
    toggleAutoTheme,
    getThemeColors,
    createCustomTheme,
    exportThemeSettings,
    importThemeSettings
};

// Color Personalization System
let currentColors = {
    accent: '#3b82f6',
    background: '#0f172a', 
    highlight: '#fbbf24'
};

// Show color picker modal
function showColorPicker() {
    console.log('🎨 Opening color picker...');
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('colorPickerModal');
    if (!modal) {
        console.log('🔧 Creating color picker modal...');
        createColorPickerModal();
        modal = document.getElementById('colorPickerModal');
    }
    
    if (modal) {
        // Load current colors
        loadCurrentColors();
        modal.style.display = 'flex';
        
        // Setup color input listeners
        setupColorInputs();
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeColorPicker();
            }
        });
        
        console.log('✅ Color picker opened');
        showNotification('🎨 Color picker opened!', 'info');
    } else {
        console.error('❌ Could not create color picker modal');
        showNotification('Color picker not available', 'error');
    }
}

// Create color picker modal dynamically
function createColorPickerModal() {
    const modalHTML = `
        <div id="colorPickerModal" class="modal-overlay" style="display: none;">
            <div class="modal color-picker-modal">
                <div class="modal-header">
                    <h3>🎨 Personalize Your Colors</h3>
                    <button class="modal-close" onclick="closeColorPicker()" aria-label="Close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="color-section">
                        <label>Accent Color (Buttons & Highlights)</label>
                        <div class="color-input-group">
                            <input type="color" id="accentColorPicker" value="#3b82f6">
                            <span class="color-preview" id="accentPreview"></span>
                        </div>
                    </div>
                    
                    <div class="color-section">
                        <label>Background Tint</label>
                        <div class="color-input-group">
                            <input type="color" id="backgroundColorPicker" value="#0f172a">
                            <span class="color-preview" id="backgroundPreview"></span>
                        </div>
                    </div>
                    
                    <div class="color-section">
                        <label>Text Highlight Color</label>
                        <div class="color-input-group">
                            <input type="color" id="highlightColorPicker" value="#fbbf24">
                            <span class="color-preview" id="highlightPreview"></span>
                        </div>
                    </div>
                    
                    <div class="preset-colors">
                        <label>Quick Presets:</label>
                        <div class="preset-grid">
                            <button class="preset-btn" onclick="applyPreset('blue')" style="background: linear-gradient(45deg, #3b82f6, #1e40af)">Blue</button>
                            <button class="preset-btn" onclick="applyPreset('purple')" style="background: linear-gradient(45deg, #8b5cf6, #7c3aed)">Purple</button>
                            <button class="preset-btn" onclick="applyPreset('green')" style="background: linear-gradient(45deg, #10b981, #059669)">Green</button>
                            <button class="preset-btn" onclick="applyPreset('orange')" style="background: linear-gradient(45deg, #f59e0b, #d97706)">Orange</button>
                            <button class="preset-btn" onclick="applyPreset('pink')" style="background: linear-gradient(45deg, #ec4899, #db2777)">Pink</button>
                            <button class="preset-btn" onclick="applyPreset('red')" style="background: linear-gradient(45deg, #ef4444, #dc2626)">Red</button>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="resetColors()">Reset to Default</button>
                    <button class="btn btn-primary" onclick="applyColors()">Apply Colors</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    console.log('✅ Color picker modal created');
}

// Close color picker modal
function closeColorPicker() {
    const modal = document.getElementById('colorPickerModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Load current colors into picker
function loadCurrentColors() {
    const saved = localStorage.getItem('studymate-custom-colors');
    if (saved) {
        currentColors = JSON.parse(saved);
    }
    
    document.getElementById('accentColorPicker').value = currentColors.accent;
    document.getElementById('backgroundColorPicker').value = currentColors.background;
    document.getElementById('highlightColorPicker').value = currentColors.highlight;
    
    updateColorPreviews();
}

// Setup color input event listeners
function setupColorInputs() {
    const inputs = ['accentColorPicker', 'backgroundColorPicker', 'highlightColorPicker'];
    
    inputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', updateColorPreviews);
        }
    });
}

// Update color previews
function updateColorPreviews() {
    const accentColor = document.getElementById('accentColorPicker').value;
    const backgroundColor = document.getElementById('backgroundColorPicker').value;
    const highlightColor = document.getElementById('highlightColorPicker').value;
    
    document.getElementById('accentPreview').style.backgroundColor = accentColor;
    document.getElementById('backgroundPreview').style.backgroundColor = backgroundColor;
    document.getElementById('highlightPreview').style.backgroundColor = highlightColor;
}

// Apply color preset
function applyPreset(presetName) {
    const presets = {
        blue: { accent: '#3b82f6', background: '#0f172a', highlight: '#60a5fa' },
        purple: { accent: '#8b5cf6', background: '#1e1b4b', highlight: '#a78bfa' },
        green: { accent: '#10b981', background: '#064e3b', highlight: '#34d399' },
        orange: { accent: '#f59e0b', background: '#431407', highlight: '#fbbf24' },
        pink: { accent: '#ec4899', background: '#4c1d95', highlight: '#f472b6' },
        red: { accent: '#ef4444', background: '#450a0a', highlight: '#f87171' }
    };
    
    const preset = presets[presetName];
    if (preset) {
        document.getElementById('accentColorPicker').value = preset.accent;
        document.getElementById('backgroundColorPicker').value = preset.background;
        document.getElementById('highlightColorPicker').value = preset.highlight;
        updateColorPreviews();
    }
}

// Apply selected colors
function applyColors() {
    const accentColor = document.getElementById('accentColorPicker').value;
    const backgroundColor = document.getElementById('backgroundColorPicker').value;
    const highlightColor = document.getElementById('highlightColorPicker').value;
    
    currentColors = {
        accent: accentColor,
        background: backgroundColor,
        highlight: highlightColor
    };
    
    // Apply colors to CSS variables
    document.documentElement.style.setProperty('--accent-primary', accentColor);
    document.documentElement.style.setProperty('--bg-primary', backgroundColor);
    document.documentElement.style.setProperty('--accent-secondary', highlightColor);
    
    // Save to localStorage
    localStorage.setItem('studymate-custom-colors', JSON.stringify(currentColors));
    
    // Close modal
    closeColorPicker();
    
    showNotification('Colors applied successfully! 🎨', 'success');
}

// Reset to default colors
function resetColors() {
    const defaultColors = {
        accent: '#3b82f6',
        background: '#0f172a',
        highlight: '#fbbf24'
    };
    
    document.getElementById('accentColorPicker').value = defaultColors.accent;
    document.getElementById('backgroundColorPicker').value = defaultColors.background;
    document.getElementById('highlightColorPicker').value = defaultColors.highlight;
    
    updateColorPreviews();
    applyColors();
}

// Load saved colors on page load
function loadSavedColors() {
    const saved = localStorage.getItem('studymate-custom-colors');
    if (saved) {
        const colors = JSON.parse(saved);
        document.documentElement.style.setProperty('--accent-primary', colors.accent);
        document.documentElement.style.setProperty('--bg-primary', colors.background);
        document.documentElement.style.setProperty('--accent-secondary', colors.highlight);
    }
}

// Make functions available globally
window.showColorPicker = showColorPicker;
window.closeColorPicker = closeColorPicker;
window.applyPreset = applyPreset;
window.applyColors = applyColors;
window.resetColors = resetColors;

// Load saved colors on page load
document.addEventListener('DOMContentLoaded', loadSavedColors);