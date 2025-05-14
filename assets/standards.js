// JavaScript para o módulo de consulta de normas técnicas

// Função para alternar o modo de tela cheia do visualizador de normas
window.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na página de consulta de normas
    if (window.location.pathname.includes('/consulta-normas')) {
        // Adicionar listener para o botão de tela cheia
        document.addEventListener('click', function(event) {
            // Verificar se o clique foi no botão de tela cheia
            if (event.target.closest('#standards-fullscreen-button')) {
                toggleFullscreen();
            }
        });
    }
});

// Função para alternar o modo de tela cheia
function toggleFullscreen() {
    const contentContainer = document.getElementById('standards-content-container');

    if (!contentContainer) return;

    // Verificar se já está em modo de tela cheia
    const isFullscreen = contentContainer.classList.contains('fullscreen-mode');

    if (isFullscreen) {
        // Sair do modo de tela cheia
        contentContainer.classList.remove('fullscreen-mode');
        contentContainer.style.position = '';
        contentContainer.style.top = '';
        contentContainer.style.left = '';
        contentContainer.style.width = '';
        contentContainer.style.height = '';
        contentContainer.style.maxHeight = '800px';
        contentContainer.style.zIndex = '';
        contentContainer.style.background = '';
        contentContainer.style.padding = '';

        // Atualizar ícone do botão
        const button = document.getElementById('standards-fullscreen-button');
        if (button) {
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-expand';
            }
            button.title = 'Expandir visualizador';
        }
    } else {
        // Entrar no modo de tela cheia
        contentContainer.classList.add('fullscreen-mode');
        contentContainer.style.position = 'fixed';
        contentContainer.style.top = '0';
        contentContainer.style.left = '0';
        contentContainer.style.width = '100vw';
        contentContainer.style.height = '100vh';
        contentContainer.style.maxHeight = 'none';
        contentContainer.style.zIndex = '9999';
        contentContainer.style.background = 'white';
        contentContainer.style.padding = '20px';
        contentContainer.style.overflow = 'auto';

        // Atualizar ícone do botão
        const button = document.getElementById('standards-fullscreen-button');
        if (button) {
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-compress';
            }
            button.title = 'Reduzir visualizador';
        }
    }
}

// Função para destacar termos de busca no conteúdo
function highlightSearchTerms() {
    // Verificar se estamos na página de consulta de normas
    if (!window.location.pathname.includes('/consulta-normas')) return;

    // Obter o termo de busca da URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('search');

    if (!searchTerm) return;

    // Obter o conteúdo da norma
    const contentElement = document.getElementById('standards-content-display');
    if (!contentElement) return;

    // Destacar o termo de busca
    const content = contentElement.innerHTML;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const highlightedContent = content.replace(regex, '<span class="search-highlight">$1</span>');

    // Atualizar o conteúdo
    contentElement.innerHTML = highlightedContent;
}

// Executar a função de destaque quando a página carregar
window.addEventListener('load', highlightSearchTerms);

// Executar a função de destaque quando o conteúdo for atualizado usando MutationObserver (moderno)
// em vez do obsoleto DOMSubtreeModified
window.addEventListener('DOMContentLoaded', function() {
    const contentElement = document.getElementById('standards-content-display');
    if (contentElement) {
        // Configurar o MutationObserver para observar mudanças no conteúdo
        const observer = new MutationObserver(function(mutations) {
            highlightSearchTerms();
        });

        // Iniciar a observação do elemento com configuração para observar mudanças no conteúdo
        observer.observe(contentElement, {
            childList: true,    // Observar adições/remoções de nós filhos
            subtree: true,      // Observar toda a subárvore
            characterData: true // Observar mudanças no conteúdo de texto
        });
    }
});
