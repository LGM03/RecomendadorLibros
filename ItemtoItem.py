#Esta modulo contiene funciones para recomendar libros basados en similitud de géneros con pesos
#y para explicar las recomendaciones generadas
#Se incluye el codigo completo con la generacion del grafo 
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import requests
import sbc_tools as sbc
from pyparsing import deque
import random


URL_PROPIA = "http://librosxxi.org/book/"
ONTO = Namespace("http://librosxxi.org/book-ontology/") 
UMBRAL_JACCARD = 0.3

def find_path_and_distance(graph, book1_uri, book2_uri, max_depth=10):
    # Construir el grafo de adyacencia basado en géneros y subclases
    if book1_uri == book2_uri:
        return 0, [book1_uri]
    
    adj_graph = {}
    def add_edge(u, v):
        adj_graph.setdefault(u, set()).add(v)
        adj_graph.setdefault(v, set()).add(u)

    for s, p, o in graph.triples((None, ONTO.tieneGenero, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef): add_edge(s, o)
        
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef): add_edge(s, o)

    visited = {book1_uri}
    queue = deque([(book1_uri, 0, [book1_uri])])

    while queue:
        current, distance, path = queue.popleft()
        if distance >= max_depth: continue

        for neighbor in adj_graph.get(current, set()):
            if neighbor == book2_uri:
                return distance + 1, path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1, path + [neighbor]))
    
    return -1, []


# Recomendador basado en pesos para libros
def recommend_weighted_books(graph, target_book_uri, top_n=5, randomness=0.1):

    WEIGHT_AUTHOR = 0.5    #mucha importancia si es el mismo autor
    WEIGHT_PUBLISHER = 0.2 #importancia media si es la misma editorial
    #la similitud de genero (distancia) será la base (máximo 1.0)
    
    all_books = set()
    for s, p, o in graph.triples((None, RDF.type, ONTO["LibrosXXI"])):
        if s != target_book_uri:
            all_books.add(s)
            
    #extraer metadatos del libro objetivo para comparar
    target_authors = set(graph.objects(target_book_uri, ONTO.tieneAutor))
    target_pub = graph.value(target_book_uri, ONTO.tieneEditorial)

    candidates = []
    for book_uri in all_books:
        # simlitud del genero 
        dist, path = find_path_and_distance(graph, target_book_uri, book_uri)
        if dist == -1: continue # Si no hay conexión alguna, ignorar
        
        genre_sim = 1 / (dist + 1)
        
        #Bonus por autores, tiene en cuenta si hay varios
        author_bonus = 0
        current_authors = set(graph.objects(book_uri, ONTO.tieneAutor))
        if target_authors.intersection(current_authors):
            author_bonus = WEIGHT_AUTHOR
            
        #bonus por editorial
        pub_bonus = 0
        current_pub = graph.value(book_uri, ONTO.tieneEditorial)
        if target_pub and current_pub and target_pub == current_pub:
            pub_bonus = WEIGHT_PUBLISHER
            
        # añadir un componente de aleatoriedad 
        luck = random.uniform(0, randomness)
        final_score = genre_sim + author_bonus + pub_bonus + luck
        
        label = graph.value(book_uri, RDFS.label) or str(book_uri).split('=')[-1]
        candidates.append({
            'label': label,
            'score': round(final_score, 3),
            'reasons': {
                'same_author': author_bonus > 0,
                'same_pub': pub_bonus > 0,
                'genre_dist': dist, 
                'path': path
            }
        })

    #ordenar y devolver las top_n recomendaciones
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]

# Función para procesar las recomendaciones e imprimirlas de forma comprensilbe
def explain_recommendations(graph, target_book_uri, recommendations):
    target_label = graph.value(target_book_uri, RDFS.label) or "Libro seleccionado"
    print(f"\n--- Explicación para: {target_label} ---")
    
    for rec in recommendations:
        print(f"\nRECOMENDACIÓN: {rec['label']} (Score: {rec['score']})")
        
        # Explicar Género y Camino
        path = rec['reasons']['path']
        dist = rec['reasons']['genre_dist']
        
        labels_path = []
        for uri in path:
            l = graph.value(uri, RDFS.label)
            labels_path.append(str(l) if l else str(uri).split('/')[-1])
        
        print(f"  • Género: Distancia {dist}. Camino semántico: {' -> '.join(labels_path)}")
    
        if rec['reasons']['same_author']:
            print(f"  • Bonus Autor: Coincidencia de autor detectada (+0.5)")
        if rec['reasons']['same_pub']:
            print(f"  • Bonus Editorial: Ambos publicados por la misma editorial (+0.2)")
