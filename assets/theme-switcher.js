/**
 * theme-switcher.js
 * Script para alternar entre os temas claro e escuro
 * Inclui persistência da preferência do usuário e transição suave entre temas
 */

// Constantes
const THEME_STORAGE_KEY = 'theme';
const LIGHT_THEME_CLASS = 'light-theme';
const DARK_THEME = 'dark';
const LIGHT_THEME = 'light';
const TRANSITION_DURATION = 300; // ms

/**
 * Alterna entre os temas claro e escuro
 * Adiciona uma transição suave e salva a preferência do usuário
 */
function toggleTheme() {
    const body = document.body;

    // Adiciona classe de transição para suavizar a mudança
    body.classList.add('theme-transition');

    // Verifica se o tema atual é claro
    if (body.classList.contains(LIGHT_THEME_CLASS)) {
        // Muda para o tema escuro
        body.classList.remove(LIGHT_THEME_CLASS);
        // Salva a preferência no localStorage
        localStorage.setItem(THEME_STORAGE_KEY, DARK_THEME);
        // Atualiza o ícone e o texto do botão
        updateThemeButton(false);
    } else {
        // Muda para o tema claro
        body.classList.add(LIGHT_THEME_CLASS);
        // Salva a preferência no localStorage
        localStorage.setItem(THEME_STORAGE_KEY, LIGHT_THEME);
        // Atualiza o ícone e o texto do botão
        updateThemeButton(true);
    }

    // Remove a classe de transição após a conclusão da animação
    setTimeout(() => {
        body.classList.remove('theme-transition');
    }, TRANSITION_DURATION);
}

// Função para atualizar o botão de tema
function updateThemeButton(isLight) {
    const themeToggleIcon = document.getElementById('theme-toggle-icon');
    const themeToggleText = document.getElementById('theme-toggle-text');

    if (themeToggleIcon && themeToggleText) {
        if (isLight) {
            themeToggleIcon.className = 'fas fa-moon me-1'; // Adicionado 'me-1' para espaçamento
            themeToggleText.textContent = 'Tema Escuro';
        } else {
            themeToggleIcon.className = 'fas fa-sun me-1'; // Adicionado 'me-1' para espaçamento
            themeToggleText.textContent = 'Tema Claro';
        }
    }
    // Removido o aviso de console quando o botão não é encontrado
}

/**
 * Aplica o tema salvo no localStorage ou o tema padrão (escuro)
 */
function applyInitialTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    const body = document.body;

    console.log('Applying initial theme. Saved theme:', savedTheme);

    if (savedTheme === LIGHT_THEME) {
        body.classList.add(LIGHT_THEME_CLASS);
        updateThemeButton(true);
    } else {
        // Assume dark theme as default
        body.classList.remove(LIGHT_THEME_CLASS);
        updateThemeButton(false);
        // Explicitamente salvar dark como padrão se não houver nada salvo
        if (!savedTheme) {
            localStorage.setItem(THEME_STORAGE_KEY, DARK_THEME);
        }
    }
}

// Aplicar o tema quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded. Applying theme and attaching listener.');
    // Aplicar o tema salvo
    applyInitialTheme();

    // Adicionar evento de clique ao botão de alternar tema
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
         // Remove listener antigo antes de adicionar novo, se já existir
        if (themeToggle._clickListener) {
             themeToggle.removeEventListener('click', themeToggle._clickListener);
             themeToggle._clickListener = null; // Limpa a referência antiga
        }
        themeToggle.addEventListener('click', toggleTheme);
        themeToggle._clickListener = toggleTheme; // Armazena a referência atual
    }
    // Removido o aviso de console quando o botão não é encontrado
});

/**
 * Reaplica o tema e reanexa o listener quando o Dash atualiza o DOM
 * Isso é necessário porque o Dash pode reconstruir partes da página
 */
let observerAttached = false; // Flag para evitar múltiplos observers

function setupObserver() {
    if (observerAttached) return;

    const observer = new MutationObserver(function(mutationsList) {
        // Otimização: Verificar se o botão de tema está presente e sem listener
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle && !themeToggle._clickListener) {
            console.log('Mutation detected. Re-attaching theme listener and applying theme.');

            // Remove listener antigo (segurança extra)
            if (themeToggle._clickListener) {
                themeToggle.removeEventListener('click', themeToggle._clickListener);
            }
            // Reanexa listener
            themeToggle.addEventListener('click', toggleTheme);
            themeToggle._clickListener = toggleTheme;

            // Reaplica o tema correto para garantir consistência
            const currentTheme = localStorage.getItem(THEME_STORAGE_KEY) || DARK_THEME;
            if (currentTheme === LIGHT_THEME) {
                 document.body.classList.add(LIGHT_THEME_CLASS);
                 updateThemeButton(true);
            } else {
                 document.body.classList.remove(LIGHT_THEME_CLASS);
                 updateThemeButton(false);
            }
        }
    });

    // Inicia a observação do body
    observer.observe(document.body, { childList: true, subtree: true });
    observerAttached = true;
    console.log('MutationObserver for theme attached.');
}

// Garante que o observer seja configurado após o carregamento inicial
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupObserver);
} else {
    setupObserver(); // Setup immediately if already loaded
}
