# Classificação dos Personagens de "Os Simpsons"
Este projeto visa estudar algoritmos de aprendizagem de máquina, criando uma simples framework para ser usada no treinamento e classificação de objetos. Iniciando com o icónico seriado norte-americano "Os Simpsons". 

# Passos iniciais
### Instalação
Baixe o projeto na sua máquina, entre no diretório do projeto e com a ferramenta `pip` instalada, execute em um terminal:
```bash
$ pip install -r requirements.txt
```

### Criando os dados de treinamento
Para isso usaremos o método `FeaturesExtractor`, que nos permite configurar como o algoritmo irá extrair as características das imagens no dataset.

Dê uma olhada no arquivo de configuração de [exemplo](/examples/feature-extraction.json). Ali apresenta uma forma básica de como configurar o extrator. Com o arquivo de configuração montado, basta chamar o módulo de extração passando o arquivo como parâmetro:
```bash
$ python ml_project/extract.py -c examples/feature-extraction.json
```

### Fazendo a classificação
Usando o módulo de classificação, é possível prover um arquivo de treinamento e obter algumas informações sobre a unidade treinada, como a matriz de confusão e as probalidades de uma determinada imagem.
```bash
$ python ml_project/classify.py -m -p /caminho/para/imagem.png -c examples/feature-extraction.json arquivo-treinamento.csv
```