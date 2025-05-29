# 📧 Email Automation Tool

Uma ferramenta automatizada para gerenciar solicitações de pagamento e reembolso, desenvolvida para a Central Estudantil.

## ✨ Funcionalidades

- 🤖 Automação de envio de emails via Gmail
- 📊 Gerenciamento de histórico de solicitações
- 📝 Interface gráfica intuitiva
- 🔄 Fluxo de trabalho otimizado para solicitações
- 📁 Integração com Google Drive
- 📈 Histórico de compras e solicitações

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/email-automation.git
cd email-automation
```

2. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

1. Crie um arquivo `.env` na raiz do projeto:
```bash
touch .env  # Linux/Mac
# ou
type nul > .env  # Windows
```

2. Adicione suas credenciais do Gmail no arquivo `.env`:
```env
EMAIL_USER=seu.email@gmail.com
EMAIL_PASSWORD=sua_senha
```

> **⚠️ Importante**: Para o `EMAIL_PASSWORD`, você precisa usar uma "Senha de App" do Google:
> 1. Acesse sua [Conta Google](https://myaccount.google.com/)
> 2. Vá em "Segurança"
> 3. Ative a verificação em duas etapas (se ainda não estiver ativa)
> 4. Em "Senhas de app", gere uma nova senha para este aplicativo
> 5. Use esta senha gerada no arquivo `.env`

## 🎮 Como Usar

1. Execute o programa:
```bash
python email_automation.py
```

2. Siga o fluxo de trabalho na interface:
   - Etapa 1: Link do Drive e Acesso a Documentos
   - Etapa 2: Informações da Compra
   - Etapa 3: Compor e Enviar Email

3. O sistema irá:
   - Abrir o Gmail automaticamente
   - Preencher o email com as informações fornecidas
   - Permitir revisão manual antes do envio

## 📋 Requisitos

- Python 3.8+
- Google Chrome instalado
- Conta Gmail com verificação em duas etapas ativada
- Acesso ao Google Drive

## 🛠️ Tecnologias Utilizadas

- Python
- Tkinter
- Selenium
- Google Chrome WebDriver
- Python-dotenv

## 📝 Notas Importantes

- Mantenha suas credenciais seguras
- Não compartilhe seu arquivo `.env`
- Verifique sempre os dados antes de enviar
- Mantenha o Chrome atualizado

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Suporte

Para suporte, envie um email para seu-email@dominio.com ou abra uma issue no GitHub.
