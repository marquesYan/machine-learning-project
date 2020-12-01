from sklearn.preprocessing import LabelEncoder
import pandas
import numpy


def prepare_data(encode_X=True):
    # carrega dataset em memória
    df = pandas.read_csv('vendas_de_jogo.csv', sep=';')
    old_shape = df.shape
    print(old_shape)

    # remove as linhas com atributos vazios 
    df.dropna(inplace=True)
    print(df.shape)
    print(f'removidos: {old_shape[0] - df.shape[0]}')

    # separa amostra
    X = df.iloc[1:, 2:]
    y = numpy.array(X.keys())

    if encode_X:
        # transforma colunas em texto para equivalente númerico
        l = LabelEncoder()

        matrice_idxs = [
            ('Plataforma', 0),
            ('Genero', 2),
            ('Editora', 3),
        ] 

        for name, index in matrice_idxs:
            numbers = l.fit_transform(X.iloc[:, index].values)
            size = max(numbers)
            print(f'{name} possui {size} diferentes valores')
            X.iloc[:, index] = numbers

    return X, y


class StepCounter:
    def __init__(self, *mixed_breakpoints):
        self._mixed_breakpoints = mixed_breakpoints

    def build_metadata(self, collection):
        # ordena o conjunto de forma ascendente
        # necessário para construir os metadados
        collection_asc = sorted(collection)

        boundaries = []
        for until, step in self._mixed_breakpoints:
            # encontra em qual indice da lista os valores
            # ainda são menores que "until"
            value_index = 0
            while collection_asc[value_index] < until:
                value_index += 1

            if step is None:
                # o limite é apenas o "until"
                boundaries.append(until)
            else:
                # conjunto de valores até o valor de "until"
                split_collection = collection_asc[:value_index]

                # encontra quantas classes para o conjunto
                found_classes = self.find_classes_from(step, split_collection)

                # acrescenta vários limites de acordo com as classes
                found_boundaries = self.find_boundaries_from(split_collection, 
                                                             found_classes,
                                                             step)
                boundaries.extend(found_boundaries)

            # remove o conjunto que acabou de ser percorrido
            # já que não há necessidade de percorrer estes novamente
            collection_asc = collection_asc[value_index:]

        # pré processa os limites, removendo valores
        # duplicados e ordenando de forma ascendente
        correct_boundaries = list(set(boundaries))
        correct_boundaries.sort()
        
        return correct_boundaries

    def find_classes_from(self, step_count, collection):
        '''Encontra o número de classes dentro do conjunto'''

        # valores mínimo e máximo da coleção de valores
        min_v, max_v = min(collection), max(collection)

        # espaço disponível para classificação
        space = int(max_v) - int(min_v)

        # calcula as classes, baseado em quantos passos são necessários 
        # para categorizar
        return int(space / step_count)

    def find_boundaries_from(self, collection, classes, step):
        '''Cria lista de limites de acordo com as classes'''

        min_value = min(collection)
        return [self.calc_boundary(min_value, class_id, step)
                for class_id in range(classes)]

    def calc_boundary(self, minimum_value, class_id, step):
        '''Calcula o valor limite da classe'''

        return minimum_value + class_id * step


class ClassSpliter:
    def __init__(self, name, *mixed_breakpoints):
        self.name = name
        self._counter = StepCounter(*mixed_breakpoints)
        self._classes, self._labels, self._boundaries = None, None, None 

    def fit_transform(self, collection, **kwargs):
        return self.fit(collection).transform(collection, **kwargs)

    def fit(self, collection):
        '''Calcula as classes, labels e limites das classes'''

        min_v, max_v = min(collection), max(collection)

        # calcula as classes, baseado em quantos passos são necessários 
        # para categorizar
        self._boundaries = self._counter.build_metadata(collection)

        # etiquetas de cada classe
        self._labels = []
        label_template = f'{self.name}[{{}} - {{}}]'
        for index, boundary in enumerate(self._boundaries):
            if index == 0:
                base_value = min_v
            else:
                base_value = self._boundaries[index - 1]
            label = label_template.format(base_value, boundary) 
            self._labels.append(label)

        # a última label não segue o limite
        # pois ela passou dos limites ;)
        self._labels.append(label_template.format(self._boundaries[-1], max_v))

        # o número de classes corresponde ao de etiquetas
        self._classes = range(len(self._labels))

        return self

    def transform(self, collection, as_label=False):
        '''Re-cria a lista com os ids das classes correspondentes'''

        # decide qual lista será a provedora das informações
        provider = self._labels if as_label else self._classes

        # número de ids de classes
        classes_len = len(provider) - 1

        def classify(value):
            # indice inicial
            index = 0

            # classe inicial
            class_ = provider[index]
            
            # pula para a proxima classe enquanto:
            #  - não está na ultima classe
            #  - valor é maior que o limite da classe
            while index < classes_len and value > self._boundaries[index]:
                index += 1
                class_ = provider[index]
            return class_

        new_collection = []
        for value in collection:
            new_collection.append(classify(value))
        return new_collection
