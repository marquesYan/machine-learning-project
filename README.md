# Passos iniciais
### Instalação
Baixe o projeto na sua máquina, entre no diretório do projeto e com o python 3 instalado, execute em um terminal:
```bash
$ python -m pip install -r requirements.txt
```

# Classificação de sons de cães e gatos
Neste trabalho foi usado a rede neural artificial para a classificação de áudios de cães e gatos. Para tal objetivo, foi necessário a extração das seguintes características dos áudios do dataset de treinamento:
- [cromagrama constante-Q](https://librosa.org/doc/main/generated/librosa.feature.chroma_cqt.html#librosa.feature.chroma_cqt)
- [mfcc](https://librosa.org/doc/main/generated/librosa.feature.mfcc.html#librosa.feature.mfcc)
- [contraste espectral](https://librosa.org/doc/main/generated/librosa.feature.spectral_contrast.html#librosa.feature.spectral_contrast) 

Estas características foram obtidas através de tentativa e erro, apesar de ter sido feito um estudo mais aprofundado para entender sobre as peculiaridades de objetos sonoros. Os vinte coeficientes do mfcc se mostraram bastante relevantes para a classificação.

Para calcular o valor de cada característica, uma matriz NxN, é usada a média aritmética dos valores da matriz.

## Criando os dados de treinamento
Primeiro extraia o dataset para um diretório nessa estrutura:
```
 - dataset
    |____ cats_and_dogs
```

Para a extração, será usado o método `AudioExtractor`, que irá buscar pelas características mencionadas acima. 

Pegaremos como exemplo [este](https://github.com/marquesYan/machine-learning-project/blob/master/ml-cats-dogs.json) arquivo de configuração, sendo que é possível alterar o parâmetro `classifier_kwargs` para suas necessidades. Quaisquer paramêtros previstos na [documentação](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html) do classificador perceptron de multi camadas, deve ser suportado neste paramêtro, assim como os solicitados no trabalho:
  - taxa de aprendizagem: `learning_rate_init`
  - iterações: `max_iter`

No mesmo arquivo de configuração é possível alterar o nome do arquivo de saída da extração, no paramêtro `method_options.feature.output`. Note que está sem a extensão, pois como o formato selecionado é `all` (todos), será exportado tanto para csv como arff.

Para iniciar a extração das características, execute no terminal:
```bash
$ python ml_project/extract.py -c ml-cats-dogs.json
```

Na tela será mostrado o status de progresso da extração. Ao finalizar, os arquivos extraídos estarão disponíveis para usarmos na classificação.

## Classificando como cão ou gato
Para fazer a classificação, deve-se informar qual áudio classficar, e de qual base de treinamento.
As opções são:
  - `-p`: caminho até o áudio a ser testado.
  - `-c`: o arquivo de configuração contendo qual classificador usar, pelo paramêtro `classifier`. Neste caso estaremos usando o `mlp` (Multi Layer Perceptron).
  - e o último argumento é o arquivo de treinamento em formato csv.

```bash
$ python ml_project/classify.py -p audio.wav -c ml-cats-dogs.json arquivo-treinamento.csv
```

# Classificação dos Personagens de "Os Simpsons"
Este projeto visa estudar algoritmos de aprendizagem de máquina, criando uma simples framework para ser usada no treinamento e classificação de objetos. Iniciando com o icónico seriado norte-americano "Os Simpsons". 

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