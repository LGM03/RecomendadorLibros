from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD
from pyvis.network import Network
import networkx as nx
import os
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
import webbrowser
data_path = "data"

def get_data_path():
    return data_path

def load(filename, format="turtle", folder=data_path):
    g = Graph()
    file_path = os.path.join(folder, filename)
    g.parse(file_path, format=format)
    return g

def save(graph, filename, format="turtle", folder=data_path):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        filepath = os.path.join(folder, filename)
        graph.serialize(destination=filepath, format=format)
        print(f"Ontología guardada en: {filepath}")
    except Exception as e:
        print(f"Error guardando ontología: {e}")

def show_graph(graph, output_file="grafo.html", height="1000px", width="100%", select_menu=True, filter_menu=True, folder="out"):
    """
    Visualiza el grafo RDF usando PyVis.
    
    :param graph: Grafo RDF de rdflib
    :param output_file: Nombre del archivo HTML de salida
    """ 
    nx_graph = nx.DiGraph()  # Dirigido porque RDF es direccional

    for sujeto, predicado, objeto in graph:
        
        # Simplificar URIs para mejor legibilidad
        s_label = str(sujeto).split("/")[-1] if "/" in str(sujeto) else str(sujeto)
        p_label = str(predicado).split("/")[-1] if "/" in str(predicado) else str(predicado)
        p_label = p_label.split("#")[-1] if "#" in p_label else p_label
        o_label = str(objeto).split("/")[-1] if "/" in str(objeto) else str(objeto)

        # Añadir arista con el predicado como atributo
        nx_graph.add_edge(s_label, o_label, label=p_label, predicate=str(p_label))


    net = Network(directed = True, neighborhood_highlight=True, select_menu=select_menu,filter_menu=filter_menu,
                height="1000px", width="100%", bgcolor="#222222", font_color="white", cdn_resources='in_line')
    net.from_nx(nx_graph)

    if not os.path.exists(folder):
        os.makedirs(folder)
    
    filepath = folder + "/" + output_file
    print(filepath)
    html = net.generate_html()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Abrir en el navegador automáticamente
    webbrowser.open(f"file://{os.path.abspath(filepath)}")
    
    #filepath =   "/".join(folder, output_file)
    #net.save_graph(filepath)
    # Abrir en el navegador automáticamente
    #os.system('open file://' + os.path.realpath(filepath))

def print_ontology_stats(graph):
    """Muestra estadísticas de la ontología generada"""
    print(f"\n=== Estadísticas de la Ontología ===")
    print(f"Total de triples: {len(graph)}")
    
    # Contar clases
    classes = list(graph.subjects(RDF.type, OWL.Class))
    print(f"Clases OWL: {len(classes)}")
    
    # Contar propiedades
    properties = list(graph.subjects(RDF.type, OWL.ObjectProperty))
    print(f"Propiedades de objeto: {len(properties)}")
    
    # Contar instancias (entidades que son instancias de alguna clase)
    instances = set()
    for s, p, o in graph.triples((None, RDF.type, None)):
        if o != OWL.Class and o != OWL.ObjectProperty and o != OWL.Ontology:
            instances.add(s)
    print(f"Instancias: {len(instances)}")
    
    # Contar relaciones subClassOf
    subclass_relations = list(graph.triples((None, RDFS.subClassOf, None)))
    print(f"Relaciones de subclase: {len(subclass_relations)}")

def print_class_hierarchy(graph):
    """
    Imprime la jerarquía de clases de forma tabulada
    Muestra las propiedades de cada categoría y las entidades descargadas
    """
    print("\n" + "=" * 80)
    print("JERARQUÍA DE CLASES DE LA ONTOLOGÍA")
    print("=" * 80)
    
    # Obtener todas las clases
    classes = set(graph.subjects(RDF.type, OWL.Class))
    
    # Encontrar clases raíz (sin padre o cuyo padre no está en el grafo)
    root_classes = []
    for cls in classes:
        parents = list(graph.objects(cls, RDFS.subClassOf))
        if not parents or not any(p in classes for p in parents):
            root_classes.append(cls)
    
    # Si no hay raíces claras, tomar todas las clases
    if not root_classes:
        root_classes = list(classes)
    
    # Imprimir cada árbol desde sus raíces
    visited = set()
    for root in root_classes:
        _print_class_subtree(graph, root, 0, visited)

def _print_class_subtree(graph, class_uri, indent_level, visited):
    """
    Método auxiliar recursivo para imprimir un subárbol de clases
    """
    if class_uri in visited:
        return
    visited.add(class_uri)
    
    # Obtener QID y label de la clase
    class_qid = str(class_uri).split('/')[-1]
    class_label = _get_label(graph, class_uri)
    
    # Obtener propiedades de esta clase
    properties = _get_class_properties(graph, class_uri)
    property_ids = [str(p).split('/')[-1] for p in properties]
    
    # Imprimir la clase con sus propiedades
    indent = "  " * indent_level
    prop_str = f" [{', '.join(property_ids)}]" if property_ids else ""
    print(f"{indent}📁 {class_label} ({class_qid}){prop_str}")
    
    # Obtener y mostrar instancias de esta clase
    instances = _get_class_instances(graph, class_uri)
    if instances:
        for instance_uri in instances:
            instance_qid = str(instance_uri).split('/')[-1]
            instance_label = _get_label(graph, instance_uri)
            print(f"{indent}  └─ {instance_qid}: {instance_label}")
    
    # Obtener subclases directas
    subclasses = list(graph.subjects(RDFS.subClassOf, class_uri))
    
    # Imprimir recursivamente cada subclase
    for subclass in subclasses:
        _print_class_subtree(graph, subclass, indent_level + 1, visited)

def _get_label(graph, uri):
    """Obtiene el label de un recurso"""
    labels = list(graph.objects(uri, RDFS.label))
    if labels:
        return str(labels[0])
    return "Sin etiqueta"

def _get_class_properties(graph, class_uri):
    """Obtiene las propiedades asociadas a una clase (rdfs:domain)"""
    properties = []
    for prop in graph.subjects(RDFS.domain, class_uri):
        if (prop, RDF.type, OWL.ObjectProperty) in graph:
            properties.append(prop)
    return properties

def _get_class_instances(graph, class_uri):
    """Obtiene las instancias de una clase"""
    instances = list(graph.subjects(RDF.type, class_uri))
    # Filtrar para asegurar que no son clases u otros recursos especiales
    instances = [i for i in instances 
                if (i, RDF.type, OWL.Class) not in graph 
                and (i, RDF.type, OWL.ObjectProperty) not in graph]
    return instances


def print_matrix(labels, matrix, col_width=30):
    print(f"{'':{col_width}}", end='')
    for p in labels:
        print(f"{p:{col_width}}", end='')
    print()
    
    for i, p1 in enumerate(labels):
        print(f"{p1:{col_width}}", end='')
        for j, p2 in enumerate(labels):
            label = matrix[i][j]
            print(f"{label:{col_width}} ", end='')
        print()