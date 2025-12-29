# minecraft-server-monitoring

### Python venv

create venv:
```sh
python3.12 -m venv .venv
```

activate venv:
```sh
source .venv/bin/activate
```

install dependencies:
```sh
pip install -r requirements.txt
```

deactivate venv:
```sh
deactivate
```

### Docker

run docker compose for dev purposes:
```sh
docker compose -f docker-compose.dev.yml up --build
```
