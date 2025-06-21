# Sistema de Gerenciamento de Outdoors Digitais

Sistema web para gerenciamento de anúncios em outdoors digitais, permitindo que clientes cadastrem e gerenciem seus anúncios e outdoors.

## Funcionalidades

- Autenticação de usuários (clientes)
- Cadastro e gerenciamento de outdoors
- Upload e gerenciamento de anúncios (imagens e vídeos)
- Vinculação de anúncios aos outdoors
- Visualização dos anúncios em tela cheia
- Interface responsiva e amigável

## Tecnologias Utilizadas

- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Banco de Dados:** Arquivos JSON locais (`usuarios.json`, `outdoors.json`, `anuncios.json`)
- **WebSockets:** Para atualizações em tempo real
- **Deploy:** Render (PaaS)

## Requisitos

- Python 3.8 ou superior
- Gunicorn
- Eventlet
- Veja `requirements.txt` para a lista completa de dependências

## Instalação e Execução Local

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd outdoor
```

2. Crie e ative um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: .\venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` baseado no `.env.example` e configure as variáveis de ambiente:
```bash
cp .env.example .env
```

5. Crie o diretório de uploads:
```bash
mkdir uploads
```

6. Inicie o servidor de desenvolvimento:
```bash
python app.py
```

7. Acesse o sistema pelo navegador:
```
http://localhost:3000
```

## Implantação no Render

1. Crie uma conta no [Render](https://render.com/) se ainda não tiver uma.

2. Conecte seu repositório do GitHub ao Render.

3. Crie um novo **Web Service** no Render e selecione o repositório do projeto.

4. Configure o serviço com as seguintes configurações:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -c gunicorn_config.py app:app`
   - **Environment Variables:** Adicione as variáveis do arquivo `.env.example`

5. Clique em **Create Web Service** para implantar a aplicação.

6. Após a implantação, acesse a URL fornecida pelo Render.

## Uso

1. Acesse a URL da aplicação implantada.
2. Registre-se como um novo cliente (aba Registro).
3. Faça login com suas credenciais.
4. Gerencie seus outdoors e anúncios através da interface administrativa.

## Variáveis de Ambiente

Certifique-se de configurar as seguintes variáveis de ambiente no arquivo `.env` ou no painel do Render:

- `FLASK_APP`: Nome do arquivo da aplicação (geralmente `app.py`)
- `FLASK_ENV`: Ambiente de execução (`development` ou `production`)
- `SECRET_KEY`: Chave secreta para a aplicação
- `DATABASE_URL`: URL de conexão com o banco de dados
- `UPLOAD_FOLDER`: Pasta para armazenar uploads
- `JWT_SECRET_KEY`: Chave secreta para tokens JWT
- `CORS_ORIGINS`: Origens permitidas para CORS (separadas por vírgula)
3. Cadastre e gerencie seus outdoors e anúncios.
4. Vincule anúncios aos outdoors conforme necessário.

## Estrutura dos Arquivos
- `app.py`: Backend Flask e rotas da API
- `public/index.html`: Página inicial com login e registro
- `public/dashboard.html`: Painel principal do usuário
- `usuarios.json`, `outdoors.json`, `anuncios.json`: Armazenamento local dos dados

## Observações
- As senhas dos usuários são armazenadas em texto simples (apenas para fins didáticos). Para produção, recomenda-se utilizar hash de senha.
- O sistema não utiliza MongoDB nem Node.js.
- O cadastro de usuários é feito apenas pelo `index.html`.

## Licença
Projeto didático para gerenciamento de outdoors digitais.

### Como Usar

1. **Cadastro de Outdoors**
   - Clique em "Novo Outdoor"
   - Preencha os dados do outdoor (nome, localização, tipo)
   - Salve o outdoor

2. **Cadastro de Anúncios**
   - Clique em "Novo Anúncio"
   - Selecione o tipo (imagem ou vídeo)
   - Faça upload do arquivo
   - Para vídeos, defina a duração
   - Salve o anúncio

3. **Vincular Anúncios**
   - Vá para a aba "Vincular Anúncios"
   - Selecione o outdoor e o anúncio
   - Clique em "Vincular"

4. **Visualização Pública**
   - Cada outdoor possui um código público único
   - Acesse `http://localhost:3000/outdoor/[codigo]` para ver os anúncios
   - A visualização é em tela cheia e automática

## Estrutura do Projeto

```
├── src/
│   ├── models/         # Modelos do MongoDB
│   ├── routes/         # Rotas da API
│   ├── middleware/     # Middlewares
│   └── server.js       # Arquivo principal
├── public/
│   ├── uploads/        # Arquivos de mídia
│   ├── index.html      # Página inicial
│   ├── dashboard.html  # Painel de controle
│   └── outdoor.html    # Visualização pública
├── .env               # Variáveis de ambiente
└── package.json       # Dependências
```

## Segurança

- Autenticação via JWT
- Senhas criptografadas
- Validação de arquivos
- Controle de acesso baseado em perfil

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. 