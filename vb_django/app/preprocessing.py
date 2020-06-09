import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, copy


class DAGFunctions:

    @staticmethod
    def add(df, c1, c2):
        """
        :param df: Pandas DataFrame
        :param c1: Column 1 Name
        :param c2: Column 2 Name
        :return: df with c1+c2 column added
        """
        data1 = df[[c1]].to_numpy()
        data2 = df[[c2]].to_numpy()
        result = (data1 + data2).flatten()
        df.insert(df.columns.size, c1+"+"+c2, result, True)
        return df

    @staticmethod
    def subtract(df, c1, c2):
        """
        :param df: Pandas DataFrame
        :param c1: Column 1 Name
        :param c2: Column 2 Name
        :return: df with c1-c2 column added
        """
        data1 = df[[c1]].to_numpy()
        data2 = df[[c2]].to_numpy()
        result = (data1 - data2).flatten()
        df.insert(df.columns.size, c1+"-"+c2, result, True)
        return df

    @staticmethod
    def normalize(df, c):
        """
        :param df: Pandas DataFrame
        :param c: Column Name
        :return: df with c normalized column added
        """
        data = df[[c]].to_numpy()
        norm = np.linalg.norm(data)
        result = (data/norm).flatten()
        df.insert(df.columns.size, c+"n", result, True)
        return df

    @staticmethod
    def square(df, c):
        """
        :param df: Pandas DataFrame
        :param c: Column Name
        :return: df with c squared column added
        """
        data = df[[c]].to_numpy()
        result = np.square(data).flatten()
        df.insert(df.columns.size, "("+c+")^2", result, True)
        return df

    @staticmethod
    def log(df, c):
        """
        :param df: Pandas DataFrame
        :param c: Column Name
        :return: df with natural log(c) column added
        """
        data = df[[c]].to_numpy()
        result = np.log(data).flatten()
        df.insert(df.columns.size, "ln("+c+")", result, True)
        return df

    @staticmethod
    def log10(df, c):
        """
        :param df: Pandas DataFrame
        :param c: Column Name
        :return: df with log10(c) column added
        """
        data = df[[c]].to_numpy()
        result = np.log10(data).flatten()
        df.insert(df.columns.size, "log10("+c+")", result, True)
        return df


class PPNode:
    parameters = None
    function = None

    def __init__(self, f, p):
        self.function = f
        self.parameters = p

    def execute(self, df):
        self.parameters["df"] = df
        results = getattr(DAGFunctions, self.function)(**self.parameters)
        return results


class PPGraph:

    def __init__(self, data, parameters):
        self.graph = nx.DiGraph()
        self.data = copy.copy(data)
        self.parameters = parameters
        self.generate_graph()
        self.traverse()

    def generate_graph(self):
        for k, v in self.parameters["nodes"].items():
            self.graph.add_node(k, data=PPNode(v["function"], v["args"]))
        for e in self.parameters["edges"]:
            self.graph.add_edge(e[0], e[1])
        # pos = nx.spring_layout(self.graph)
        # nx.draw_networkx_nodes(self.graph, pos, node_size=700)
        # nx.draw_networkx_edges(self.graph, pos, edgelist=self.parameters["edges"], width=3)
        # nx.draw_networkx_labels(self.graph, pos, font_size=20)
        # plt.show()

    def traverse(self):
        order = list(nx.topological_sort(self.graph))
        for o in order:
            n = self.graph.nodes[o]
            self.data = n['data'].execute(self.data)


if __name__ == "__main__":
    _raw_data = pd.read_excel(os.path.join("data", "VB_Data_1a.xlsx"))                  # Data source

    # two inputs for the request: csv data and json configuration for preprocessing
    input_parameters = {
        'nodes': {
            1: {'function': 'add', 'args': {'c1': 'x1', 'c2': 'x3'}},
            2: {'function': 'square', 'args': {'c': 'x3'}},
            3: {'function': 'square', 'args': {'c': 'x1+x3'}},
            4: {'function': 'normalize', 'args': {'c': 'x5'}},
        },
        'edges': [[1, 3]]
    }

    pp_data = PPGraph(_raw_data, input_parameters).data
    print(pp_data.to_string())
