import os
from subprocess import run


IRI_base = "http://purl.obolibrary.org/obo/obi/dev/import/"
ROBOT = ["java", "-jar", "build/robot.jar", "--prefix", "REO: http://purl.obolibrary.org/obo/REO_"]


def check_file_length(path):
    size = os.path.getsize(path)
    if size == 0:
        return False
    else:
        return True


def prepare_robot_module(ontology):
    """
    Split a ROBOT import config file into build components
    """
    ontology = ontology.upper()
    source_path = os.path.join("build", f"{ontology}_import_source.owl")
    parent_tsv_path = os.path.join("build", f"{ontology}_parent.tsv")
    parent_owl_path = os.path.join("build", f"{ontology}_parent.owl")
    iri = IRI_base + f"{ontology.upper()}_imports.owl"
    args = [
        "merge",
        "--input",
        source_path,
        "template",
        "--template",
        parent_tsv_path,
        "annotate",
        "--ontology-iri",
        iri,
        "--output",
        parent_owl_path,
    ]
    command = ROBOT + args
    run(command)


def build_robot_module(ontology):
    """
    Generate the OWL file associated with a ROBOT import module
    """
    iri = IRI_base + f"{ontology}_imports.owl"
    ignore = os.path.join("build", f"{ontology}_ignore.txt")
    limit = os.path.join("build", f"{ontology}_limit.txt")
    mireot = os.path.join("build", f"{ontology}_mireot.txt")
    module = os.path.join("src", "ontology", "robot_outputs", f"{ontology}_imports.owl")
    parent = os.path.join("build", f"{ontology}_parent.owl")
    relation = os.path.join("build", f"{ontology}_relation.txt")
    source = os.path.join("build", f"{ontology}_import_source.owl")
    term = os.path.join("build", f"{ontology}_import.txt")
    mireot_args = [
        "extract",
        "--method",
        "MIREOT",
        "--input",
        source,
        "--upper-terms",
        limit,
        "--lower-terms",
        term,
        "--intermediates",
        "minimal",
        "--annotate-with-source",
        "true",
        "export",
        "--header",
        "IRI",
        "--export",
        mireot,
    ]
    subset_args = [
        "extract",
        "--method",
        "subset",
        "--input",
        source,
        "--term-file",
        mireot,
        "--term-file",
        relation,
        "--annotate-with-source",
        "true",
    ]
    remove_args = [
        "remove",
        "--term-file",
        ignore,
    ]
    filter_args = [
        "filter",
        "--include-term",
        "rdfs:label",
        "--include-term",
        "oboInOwl:id",
        "--include-term",
        "rdfs:label",
        "--include-term",
        "IAO:0000115",
        "--select",
        "annotation-properties",
        "--select",
        "complement",
    ]
    finalize_args = [
        "reduce",
        "--reasoner",
        "ELK",
        "merge",
        "--input",
        parent,
        "annotate",
        "--ontology-iri",
        iri,
        "convert",
        "-o",
        module,
    ]
    mireot_command = ROBOT + mireot_args
    subset_command = ROBOT + subset_args
    if check_file_length(ignore):
        subset_command += remove_args
    subset_command += filter_args
    subset_command += finalize_args
    run(mireot_command)
    run(subset_command)
    print(f"Wrote src/ontology/robot_outputs/{ontology}_imports.owl")


def build_ontofox_module(ontology):
    config = os.path.join("src", "ontology", "OntoFox_inputs", f"{ontology}_input.txt")
    build_module = os.path.join("build", f"{ontology}_imports.owl")
    output = os.path.join("src", "ontology", "OntoFox_outputs", f"{ontology}_imports.owl")
    args = [
        "curl",
        "-s",
        "-F",
        f"file=@{config}",
        "-o",
        build_module,
        "https://ontofox.hegroup.org/service.php",
    ]
    run(args)
    if ontology == "CLO":
        args2 = [
            "remove",
            "--input",
            build_module,
            "--select",
            "annotation-properties",
            "--trim",
            "false",
            "--output",
            output,
        ]
    else:
        args2 = ["convert", "-i", build_module, "-o", output]
    command = ROBOT + args2
    run(command)
    print(f"Wrote src/ontology/OntoFox_outputs/{ontology}_imports.owl")
