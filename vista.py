import streamlit as st
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import requests
from ItemtoItem import explain_recommendations, recommend_weighted_books
from collaborative import agregar_usuarios, obtener_info_libro, recommend_books_by_user_profile
import sbc_tools as sbc

URL_PROPIA = "http://librosxxi.org/book/"

@st.cache_resource
def cargar_grafo():
    return sbc.load("grafo_con_usuarios.html", format="turtle")

graph = cargar_grafo()

st.set_page_config(
    page_title="Sistema de Recomendación de Libros",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
    <style>
    /* Estilos generales */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Estilo para los encabezados */
    h1, h2, h3 {
        color: #1E3A8A;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Estilo para las tarjetas */
    .card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #3B82F6;
    }
    
    /* Estilo para los botones */
    .stButton > button {
        background-color: #3B82F6;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* Estilo para los campos de entrada */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E2E8F0;
    }
    
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E2E8F0;
    }
    
    /* Estilo para los selectores */
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 2px solid #E2E8F0;
    }
    
    /* Estilo para el sidebar */
    .css-1d391kg {
        background-color: #F1F5F9;
        padding: 2rem 1rem;
    }
    
    /* Contenedor de resultados */
    .result-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1.5rem;
    }
    
    /* Animación sutil para los resultados */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<h1 style='text-align: center;'>📚 Sistema de Recomendación de Libros</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 1.2rem;'>Descubre tu próximo libro favorito basado en tus preferencias</p>", unsafe_allow_html=True)

# Barra lateral para navegación
with st.sidebar:
    st.markdown("### 🔍 Modo de búsqueda")
    modo = st.radio(
        "Selecciona cómo quieres obtener recomendaciones:",
        ["📖 Por libro específico", "👤 Por perfil de usuario"]
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### ℹ️ Información")
    st.info("""
    Este sistema te ayuda a encontrar libros que podrían interesarte.
    
    - **Por libro específico**: Introduce un libro que te guste y obtén recomendaciones similares.
    
    - **Por perfil de usuario**: Comparte tus preferencias para obtener recomendaciones personalizadas.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# Contenido principal basado en la selección
if modo == "📖 Por libro específico":
    st.markdown("## 📖 Recomendaciones basadas en un libro")
 
    libro = st.text_input(
        "Introduce el título de un libro que te haya gustado:",
        placeholder="Ej: Cien años de soledad"
    )

    # Botón para obtener recomendaciones
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        buscar_recomendaciones = st.button("🔍 Buscar recomendaciones", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Área para mostrar resultados
    if buscar_recomendaciones and libro:
        libro_ejemplo = URIRef(f"{URL_PROPIA}_titulo={libro.replace(' ', '_').replace(':', '').replace(',', '').replace('(', '').replace(')', '').replace('.', '').lower()}")
        recomendacion = recommend_weighted_books(graph, libro_ejemplo, top_n=5)

        
        # Aquí normalmente se mostrarían los resultados de la lógica de recomendación
        target_label = graph.value(libro_ejemplo, RDFS.label) or "Libro seleccionado"
    
        st.markdown(f"<h2>📚 Recomendaciones para: {target_label}</h2>", unsafe_allow_html=True)

        for rec in recomendacion:
            rec_label = rec['label']
            score = rec['score']
            path = rec['reasons']['path']
            dist = rec['reasons']['genre_dist']
            same_author = rec['reasons']['same_author']
            same_pub = rec['reasons']['same_pub']
            
            # Traducir URIs a etiquetas legibles
            labels_path = []
            for uri in path:
                l = graph.value(uri, RDFS.label)
                labels_path.append(str(l) if l else str(uri).split('/')[-1])
            path_str = " → ".join(labels_path)
            
            # Construir HTML para cada recomendación
            html = f"""<div style="background-color: #f0f8ff; padding: 1rem; border-radius: 10px;">
            <h4 style="margin-bottom: 0.3rem;">{rec_label} 
            <span style="font-size:0.9rem; color:#555;">(Score: {score})</span>
            </h4>
            <p style="margin:0.2rem 0;"><strong>Camino de género:</strong> {path_str}</p>
            <p style="margin:0.2rem 0;">
            <strong>Distancia de género:</strong> {dist} <br>
            {"<span style='color:green;'>Bonus Autor: Coincide</span>" if same_author else ""}<br>
            {"<span style='color:green;'>Bonus Editorial: Coincide</span>" if same_pub else ""}"""
            st.markdown(html, unsafe_allow_html=True)

            
            st.markdown("</div>", unsafe_allow_html=True)
    
            
else:  # Modo por perfil de usuario
    st.markdown("## 👤 Recomendaciones basadas en tu perfil")
    
    # Formulario de perfil de usuario
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input("Tu nombre:", placeholder="Ej: María")
        
    with col2:
        edad = st.number_input("Tu edad:", min_value=5, max_value=100, value=25)
    
    # Campo para libros favoritos
    st.markdown("### 📖 Tus libros favoritos")
    st.markdown("Introduce algunos libros que hayas disfrutado (uno por línea):")
    libros_favoritos = st.text_area(
        "Libros favoritos:",
        placeholder="Ej: El señor de los anillos\nHarry Potter y la piedra filosofal\n1984",
        height=100
    )
    
    
    # Botón para obtener recomendaciones
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        obtener_recomendaciones = st.button("✨ Obtener recomendaciones personalizadas", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Área para mostrar resultados
    if obtener_recomendaciones and nombre:
        st.markdown(f"### 🎯 Recomendaciones personalizadas para *{nombre}*")

        #Agregar usuario. si no existe.
        agregar_usuarios(graph, {'nombre': nombre, 'edad': edad,
        'libros_gustados': [URIRef(f"{URL_PROPIA}_titulo={libro.strip().replace(' ', '_').replace(':', '').replace(',', '').replace('(', '').replace(')', '').replace('.', '').lower()}") for libro in libros_favoritos.split('\n') if libro.strip()]})

        recomendaciones = recommend_books_by_user_profile(graph, URIRef(f"{URL_PROPIA}_usuario={nombre.lower()}"), top_n=5)

        st.markdown("#### 📚 Libros recomendados para ti:")

        if not recomendaciones:
            st.info("No se encontraron recomendaciones basadas en usuarios similares.")
        else:
            for i, (libro_uri, score) in enumerate(recomendaciones):
                info = obtener_info_libro(graph, libro_uri)

                html = f"""<div style="background-color: #f0f8ff; padding: 1rem; border-radius: 10px;">
                <h4 style="margin-bottom: 0.3rem;">{info['titulo']} 
                <span style="font-size:0.9rem; color:#555;">(⭐ Score: {score})</span>
                </h4>
                <p style="margin:0.2rem 0;"><strong>Autor:</strong> {info['autor']}</p>
                <p style="margin:0.2rem 0;"><strong>Género:</strong> {info['genero']}</p>
                <p style="margin:0.2rem 0;"><strong>Año:</strong> {info['año']}</p>
                <p style="margin:0.2rem 0;">
                <p style="margin:0.2rem 0;"><strong>Editorial:</strong> {info['editorial']}</p>
                <p style="margin:0.2rem 0;"><strong>ISBN:</strong> {info['isbn']}</p>
                <p style="margin:0.2rem 0;"><strong>Clasificación:</strong> {info['mature']}</p>
                <p style="margin:0.2rem 0;"><strong>Accesibilidad EPUB:</strong> {info['epubAccesibility']}</p>
                <p style="margin:0.2rem 0;">
                <p style="margin:0.2rem 0;"><strong>Descripción:</strong> {info['description']}</p>
                """
                st.markdown(html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Sugerencia para refinar búsqueda
        st.info("💡 Para obtener recomendaciones más precisas, añade más libros a tu lista de favoritos.")

# Pie de página
st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748B;'>Sistema de Recomendación de Libros 📚</div>", unsafe_allow_html=True)