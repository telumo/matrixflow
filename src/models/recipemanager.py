import json
from pathlib import Path
import networkx as nx
from collections import defaultdict


class Manager:
    def __init__(self):
        self.recipe_dir = "./recipes"
        self.recipe = ""
        self.edge_dict = defaultdict(list)

    def load_recipe(self, recipe_path="", name="recipe.json"):
        path = Path(self.recipe_dir) / recipe_path /name
        print(path)
        with open(path, "rb") as f:
            self.recipe = json.load(f)

        for layer in self.recipe["layers"]:
            if "params" in layer:
                for k, v in layer["params"].items():
                    print(v)
                    if isinstance(v, dict) and v.get("type") == "number":
                        v["value"] = int(v["value"])
        return self.recipe

    def change_edge_sources(self, layer_id, output):
        for target, source_list in self.edge_dict.items():
            if layer_id in source_list:
                self.edge_dict[target].remove(layer_id)
                self.edge_dict[target].append(output)

    def _generate_edge_dict(self):
        edges = self.recipe["edges"]
        for e in edges:
            source = e["sourceId"]
            target = e["targetId"]
            self.edge_dict[target].append(source)
        print('"target":["source"]')
        print(self.edge_dict)

    def sort_layers(self):
        self._generate_edge_dict()
        layers = self.recipe["layers"]
        edges = self.recipe["edges"]
        ed = [(e["sourceId"], e["targetId"]) for e in edges]
        G = nx.DiGraph()
        G.add_edges_from(ed)
        sorted_edges = list(nx.topological_sort(G))
        layers_dict = {layer["id"]: layer for layer in layers}
        return sorted_edges, layers_dict
