from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import requests
import sbc_tools as sbc
from pyparsing import deque
import random

URL_PROPIA = "http://librosxxi.org/book/"
ONTO = Namespace("http://librosxxi.org/book-ontology/") 
UMBRAL_JACCARD = 0.2

#Comprobamos si el usuario existe o no, si no existe lo añadimos junto con sus gustos
#Si ya existe agregamos los posibles nuevos gustos
def agregar_usuarios(graph, usuario):
    usuario_uri = URIRef(f"{URL_PROPIA}_usuario={usuario['nombre'].lower()}")
    if (usuario_uri, RDF.type, ONTO.Usuario) not in graph:
        graph.add((usuario_uri, RDF.type, ONTO.Usuario))
        graph.add((usuario_uri, RDFS.label, Literal(usuario['nombre'])))
        graph.add((usuario_uri, ONTO.edad, Literal(usuario['edad'])))
    
    for libro_uri in usuario['libros_gustados']:

        if (libro_uri, RDF.type, ONTO.LibrosXXI) in graph and (usuario_uri, ONTO.leGusta, libro_uri) not in graph:
            graph.add((usuario_uri, ONTO.leGusta, libro_uri))

    sbc.save(graph, "grafo_recomendador.html", format="turtle")

def jaccard_users(graph, user1_uri, user2_uri):

    libros_u1 = set(graph.objects(user1_uri, ONTO.leGusta))
    libros_u2 = set(graph.objects(user2_uri, ONTO.leGusta))
    
    # Si alguno no tiene libros, no hay similitud
    if not libros_u1 or not libros_u2:
        return 0.0
    
    interseccion = libros_u1.intersection(libros_u2)
    min_size = min(len(libros_u1), len(libros_u2))
    
    if min_size == 0:
        return 0.0
    
    return round(len(interseccion) / min_size, 3)

def recommend_books_by_user_profile(graph, usuario_x, top_n=5):
    usuarios = set(graph.subjects(RDF.type, ONTO.Usuario))
    jaccard_results = []

    for user in usuarios:
        if user == usuario_x:
            continue  # Omitir el usuario de referencia
        sim = jaccard_users(graph, usuario_x, user)
        if sim > UMBRAL_JACCARD: 
            jaccard_results.append((usuario_x, user, sim))

    libros_usuario = {}
    libros_originales = set(graph.objects(usuario_x, ONTO.leGusta))

    for u1, u2, sim in sorted(jaccard_results, key=lambda x: x[2], reverse=True):
        label_u2 = graph.value(u2, RDFS.label)
        libros_usuario2= set(graph.objects(u2, ONTO.leGusta))

        for libro in libros_usuario2:
            if libro not in libros_originales:
                if libro in libros_usuario:
                    libros_usuario[libro] += sim
                else:
                    libros_usuario[libro] = sim
    return sorted(libros_usuario.items(), key=lambda x: x[1], reverse=True)[:top_n]

def rdf_to_str(graph, value, default="No especificado"):
    if value is None:
        return default

    # Literal → string directo
    if isinstance(value, Literal):
        return str(value).strip('"')

    # URI → intentar label
    if isinstance(value, URIRef):
        label = graph.value(value, RDFS.label)
        if label:
            return str(label)
        # fallback: último fragmento de la URI
        return str(value).split("/")[-1]

    return default

def limpiar_info_libro(info):
    info['description'] = info['description'].strip('"')
    info['epubAccesibility'] = "Sí" if info['epubAccesibility'].lower() == "true" else "No"
    info['mature'] = {
        "NOT_MATURE": "Apto para todo público",
        "MATURE": "Contenido para adultos"
    }.get(info['mature'], info['mature'])
    info['año'] = info['año'][:4]
    return info


def obtener_info_libro(graph, libro_uri):
    salida = {
        "titulo": rdf_to_str(graph, graph.value(libro_uri, RDFS.label), "Título desconocido"),
        "autor": rdf_to_str(graph, graph.value(libro_uri, ONTO.tieneAutor), "Autor desconocido"),
        "genero": rdf_to_str(graph, graph.value(libro_uri, ONTO.tieneGenero), "Género no especificado"),
        "editorial": rdf_to_str(graph, graph.value(libro_uri, ONTO.tieneEditorial), "Editorial no especificada"),
        "mature": rdf_to_str(graph, graph.value(libro_uri, ONTO.maturityRating), "No especificado"),
        "description": rdf_to_str(graph, graph.value(libro_uri, ONTO.description), "Sin descripción disponible"),
        "año": rdf_to_str(graph, graph.value(libro_uri, ONTO.año), "Año no especificado"),
        "epubAccesibility": rdf_to_str(graph, graph.value(libro_uri, ONTO.epubAccesibility), "No especificado"),
        "isbn": rdf_to_str(graph, graph.value(libro_uri, ONTO.isbn), "ISBN no especificado"),
    }

    return limpiar_info_libro(salida)
