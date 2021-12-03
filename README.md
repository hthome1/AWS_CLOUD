# AWS_CLOUD
Projeto de Computação em Nuvem. python + boto3 para criar e gerenciar sistema ORM


### Para rodar o projeto:

* pip install boto3

* criar arquivo em ~/.aws chamado credentials com
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

* criar arquivo em ~/.aws chamado config com
[default]
region=us-east-1

* rodar o cliente.py e depois o main.py

* Esperar o main rodar

* Para os request:
    * POST = python endpoints.py POST NOME_TASK DESCRICAO_TASK
    * GET = python endpoints.py GET
    * DELTE = python endpoints.py DELETE