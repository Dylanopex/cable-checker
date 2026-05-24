# Agent Context & Handover Notes

## 🤖 Contexto do Projeto

Este projeto foi construído para resolver um problema recorrente de roteamento do macOS: quando o Mac está conectado via cabo de rede (Ethernet) e Wi-Fi simultaneamente, e a internet do cabo falha (mas o link físico continua conectado), o macOS mantém a rota default do cabo e não chaveia o tráfego para o Wi-Fi.

O **Cable Checker** monitora essa conectividade em tempo real a cada 3 segundos, enviando um ping restrito à interface do Cabo. Se a internet falhar por 2 pings consecutivos (6 segundos), ele move o Wi-Fi para o topo de prioridade. Ao reestabelecer o cabo por 2 pings de sucesso, ele devolve a Ethernet para o topo.

---

## ⚙️ Decisões Técnicas Importantes

### 1. Compilação Robusta via `osacompile`
* **Desafio:** A compilação padrão com `py2app` falhou repetidamente com o erro genérico *"Launch error - See the py2app website for debugging launch issues"*. Isso ocorreu devido a bloqueios de assinatura e redistribuição da biblioteca padrão Python (`dyld` references) empacotada no Xcode Command Line Tools no macOS.
* **Solução:** Em vez de usar `py2app`, compilamos o aplicativo usando a ferramenta nativa do macOS **`osacompile`** (que cria uma estrutura nativa AppleScript que inicia o script em Python em background). 
* **Ocultação do Dock:** Adicionamos o parâmetro `<key>LSUIElement</key><true/>` no `Info.plist` da estrutura do `.app` final. Isso garante que ele execute em background e apareça unicamente na barra superior (Menu Bar) do macOS, sem ícone no Dock.

### 2. Interface Vetorial Customizada (`NSImage`)
* **Desafio:** Bolinhas coloridas padrão em emoji (ex: `🟢`, `🟡`, `🔴`) possuem dimensões fixas no macOS, o que gerava um visual muito grande, poluindo a barra superior e destoando de outros apps nativos.
* **Solução:** Programamos diretamente a API Cocoa do macOS (`AppKit`) em Python. Desenhamos um vetor circular anti-aliasing de **7x7 pixels** dentro de um canvas de 14x14 (`NSImage`). Isso gerou um indicador minimalista **exatamente 20% menor** que o padrão do emoji, alinhando o visual com o design premium do macOS.

### 3. Localização Dinâmica de Idioma
* **Solução:** O aplicativo lê as preferências globais do macOS (`AppleLanguages`) através de `NSUserDefaults` da biblioteca `Foundation` e ajusta os textos dinamicamente.
* **Binds de Cliques:** Como os textos mudam dinamicamente por idioma (ex: "Sair" em PT vs "Quit" em EN), removemos os decorators estáticos `@rumps.clicked(...)` e implementamos a inicialização e binds de menus de forma programática direto no construtor `__init__`.

---

## 📝 Para Futuros Agentes (Manutenção)

* **Onde fica o script final que o app executa?** O aplicativo compilado `CableChecker_vX.app` aponta e executa o script localizado na pasta segura do usuário em: `~/.cable_checker_app/cable_checker.py`. Qualquer mudança de lógica deve ser feita nesse arquivo de script local ou recompilada no Desktop.
* **Segurança e Privilégios:** O comando `networksetup -ordernetworkservices` pode pedir autenticação de senha ou Touch ID no macOS. O README instrui o usuário a adicionar o `networksetup` no arquivo `/etc/sudoers` para permitir transição instantânea e silenciosa.

---

*Desenvolvido em Maio de 2026 pelo agente Antigravity (Google DeepMind Advanced Agentic Coding).*
