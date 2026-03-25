import os
from obi.ontofox import Ontofox
from obi.owl_reader import get_term_info
from obi.util import contract, dict2TSV


def convert(ontology):
    """
    Create a ROBOT config file based on an Ontofox config file
    """
    imports = {}
    path = Ontofox.find(ontology)
    if path:
        config = Ontofox(path)
        for key, value in config.terms.items():
            curie = contract(key)
            module = os.path.join("src", "ontology", "OntoFox_outputs", f"{ontology}_imports.owl")
            try:
                term_type, label, _ = get_term_info(curie, module)
                if "owl:ObjectProperty" in term_type:
                    action = "relate"
                else:
                    action = "import"
                imports[curie] = {
                    "ontology ID": curie,
                    "label": label,
                    "action": action,
                    "logical type": "",
                    "parent class": "",
                }
            except ValueError:
                print(f"WARN: {curie} appears in OntoFox config file but not in OntoFox module")
                print(f"{curie} was not added to ROBOT config file")
        output = os.path.join("src", "ontology", "robot_inputs", f"{ontology}_input.tsv")
        dict2TSV(imports, output)
        print(f"Converted {ontology} to ROBOT")
