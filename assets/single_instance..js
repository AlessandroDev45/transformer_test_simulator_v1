// assets/single_instance.js

(function() { // IIFE to avoid polluting global scope
    const lockKey = 'transformerSimulatorInstanceLock_v1'; // Chave única no localStorage
    const maxLockAge = 15000; // Idade máxima do lock em ms (15s) antes de ser considerado "velho"
    const heartbeatFrequency = 5000; // Frequência para atualizar o timestamp (5s)

    let myToken = null; // Identificador único desta aba
    let heartbeatInterval = null; // Referência para o intervalo do heartbeat
    let isLockedByThisTab = false; // Flag para indicar se esta aba detém o lock

    // Função para gerar um token simples e único
    function generateToken() {
        return Date.now() + '-' + Math.random().toString(36).substring(2, 15);
    }

    // Função para exibir uma sobreposição de erro bloqueante
    function displayInstanceError(message) {
        console.error("Single Instance Error:", message); // Log do erro no console
        let overlay = document.getElementById('dash-instance-lock-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'dash-instance-lock-overlay';
            // Estilo básico do overlay - adapte às cores do seu tema se desejar
            Object.assign(overlay.style, {
                position: 'fixed', top: '0', left: '0', width: '100%', height: '100%',
                backgroundColor: 'rgba(40, 44, 52, 0.97)', // Fundo escuro semi-transparente
                color: '#f8f9fa', // Texto claro
                display: 'flex', flexDirection: 'column', // Empilhar verticalmente
                justifyContent: 'center', alignItems: 'center',
                zIndex: '10000', textAlign: 'center', fontSize: '16px', // Tamanho de fonte base
                padding: '20px', fontFamily: 'Arial, sans-serif',
                boxSizing: 'border-box'
            });
            document.body.appendChild(overlay);
        }
        // Conteúdo HTML da mensagem de erro
        overlay.innerHTML = `
            <div style="background-color: #dc3545; padding: 30px; border-radius: 8px; max-width: 90%; width: 550px; box-shadow: 0 5px 15px rgba(0,0,0,0.4);">
                <p style="font-size: 1.3em; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 10px;">
                    ⚠️ Instância Múltipla Detectada
                </p>
                <p style="font-size: 1em; line-height: 1.5; margin-bottom: 20px;">${message}</p>
                <p style="font-size: 0.95em; line-height: 1.4; margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                    Por favor, <strong>feche as outras janelas/abas</strong> desta aplicação e <strong>atualize (F5 ou Ctrl+R)</strong> esta página para continuar.
                 </p>
            </div>`;
        // Impede a interação com a página atrás
        document.body.style.overflow = 'hidden';
        // Para o heartbeat se a sobreposição for exibida
        stopHeartbeat();
    }

    // Função para definir ou atualizar o lock no localStorage
    function acquireOrRefreshLock() {
        const lockData = { token: myToken, timestamp: Date.now() };
        try {
            localStorage.setItem(lockKey, JSON.stringify(lockData));
            // console.log(`Lock ACQUIRED/REFRESHED by: ${myToken}`); // Comentado para reduzir logs
            isLockedByThisTab = true; // Esta aba agora detém o lock
            return true;
        } catch (e) {
            console.error('Falha ao definir/atualizar lock no localStorage:', e);
            displayInstanceError("Não foi possível acessar o armazenamento local para controlar instâncias. Verifique as permissões do navegador ou se o armazenamento está cheio.");
            isLockedByThisTab = false;
            return false;
        }
    }

    // Função para liberar o lock SOMENTE se esta aba o possuir
    function releaseLock() {
        if (!isLockedByThisTab) {
            // console.log(`Lock release skipped - not held by this tab: ${myToken}`); // Comentado
            return; // Não faz nada se esta aba não tinha o lock
        }
        try {
            const storedLockData = localStorage.getItem(lockKey);
            if (storedLockData) {
                const lock = JSON.parse(storedLockData);
                // Remove apenas se o token corresponder
                if (lock.token === myToken) {
                    localStorage.removeItem(lockKey);
                    console.log(`Lock RELEASED by: ${myToken}`);
                } else {
                    console.warn(`Lock NOT RELEASED - token mismatch on unload: myToken=${myToken}, storedToken=${lock.token}`);
                }
            }
        } catch (e) {
            console.error('Falha ao remover lock no unload:', e);
        }
        // Para o heartbeat ao fechar
        stopHeartbeat();
        isLockedByThisTab = false;
    }

    // Função para parar o heartbeat
    function stopHeartbeat() {
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
             console.log(`Heartbeat stopped for token: ${myToken}`);
        }
    }

    // Função para atualizar periodicamente o timestamp (heartbeat)
    function startHeartbeat() {
        stopHeartbeat(); // Garante que não haja intervalos duplicados
        heartbeatInterval = setInterval(() => {
            if (!isLockedByThisTab) { // Se perdeu o lock, para
                console.warn(`Heartbeat: Lock no longer held by ${myToken}. Stopping.`);
                stopHeartbeat();
                return;
            }
            try {
                // Simplesmente atualiza o lock (se ainda o detém)
                if(!acquireOrRefreshLock()) {
                    // Se falhar ao atualizar, provavelmente perdeu o lock ou houve erro
                   stopHeartbeat();
                }
                // console.log('Heartbeat: Lock timestamp updated by', myToken); // Comentado
            } catch(e) {
                console.error('Heartbeat error:', e);
                stopHeartbeat();
            }
        }, heartbeatFrequency);
        console.log(`Heartbeat started for token: ${myToken}`);
    }

    // --- Lógica Principal de Verificação ---
    function checkAndManageInstance() {
        myToken = generateToken(); // Gera token para esta instância
        console.log(`Initializing instance check - MyToken: ${myToken}`);
        let proceed = false; // Assume que não pode prosseguir por padrão

        try {
            const storedLockData = localStorage.getItem(lockKey);

            if (storedLockData) {
                const lock = JSON.parse(storedLockData);
                const lockAge = Date.now() - lock.timestamp;
                console.log(`Existing lock found: Token=${lock.token}, Age=${lockAge}ms`);

                if (lockAge > maxLockAge) {
                    // Lock existente está velho, assume o controle
                    console.warn(`Stale lock detected (token: ${lock.token}), taking over.`);
                    if (acquireOrRefreshLock()) {
                        proceed = true;
                    }
                } else {
                    // Outra instância ativa detectada
                    console.error(`Another active instance detected (token: ${lock.token})`);
                    displayInstanceError('Outra janela ou aba desta aplicação já está aberta.');
                    // proceed continua false
                }
            } else {
                // Nenhum lock existe, adquire
                console.log(`No existing lock found. Acquiring lock.`);
                if (acquireOrRefreshLock()) {
                    proceed = true;
                }
            }
        } catch (e) {
            console.error('Erro ao verificar/parsear lock do localStorage:', e);
            displayInstanceError("Erro ao verificar o bloqueio de instância. O armazenamento local pode estar corrompido ou inacessível.");
            // proceed continua false
        }

        if (proceed) {
            // Se adquiriu o lock com sucesso, configura listeners e heartbeat
            window.addEventListener('beforeunload', releaseLock);
            startHeartbeat();
            console.log("Instance check PASSED. Application can proceed.");
        } else {
             console.error("Instance check FAILED. Application loading halted by overlay.");
             stopHeartbeat(); // Garante que o heartbeat não rode se falhar
        }
    }

    // Executa a verificação após o carregamento do DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAndManageInstance);
    } else {
        checkAndManageInstance(); // Executa imediatamente se o DOM já estiver carregado
    }

})(); // Fim da IIFE
