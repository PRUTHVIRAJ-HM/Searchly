import streamlit as st
import requests
import bs4
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import base64
from PIL import Image
import io

# Set page configuration
st.set_page_config(
    page_title="Searchly",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #4285F4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5f6368;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #222831;
        border-radius: 10px;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 500;
        margin-bottom:14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4285F4 !important;
        color: white !important;
    }
    .search-button {
        background-color: #4285F4;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .search-results {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .result-header {
        color: #1a73e8;
        font-size: 1.3rem;
        margin-bottom: 10px;
    }
    .search-box {
        border-radius: 10px;
        border: 1px solid #dadce0;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'data_storage' not in st.session_state:
    st.session_state.data_storage = []
if 'data_bucket' not in st.session_state:
    st.session_state.data_bucket = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Logo and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-header">🔍 Searchly</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your multi-source search companion</p>', unsafe_allow_html=True)

# Create a sidebar for additional options
with st.sidebar:
    st.title ("🔍 Searchly") # Replace with your own logo or keep this placeholder
    st.title("Search Options")
    
    st.subheader("Search History")
    if st.session_state.search_history:
        for idx, query in enumerate(st.session_state.search_history[-5:]):
            st.write(f"{idx+1}. {query}")
    else:
        st.write("No searches performed yet.")
    
    st.divider()
    st.subheader("About")
    st.write("""
    Searchly is a powerful multi-source search tool that combines Wikipedia and DuckDuckGo search capabilities.
    
    Use it to quickly find information from reliable sources, save results, and improve your search experience.
    
    Created with ❤️ using Streamlit.
    """)

# Main tabs with custom styling
tab1, tab2, tab3 = st.tabs(["📚 Wiki Search", "🦆 AI Search", "💾 Save Data"])

# Wiki Search Tab
with tab1:
    st.header("Wikipedia Research")
    st.write("Search for in-depth information from Wikipedia's vast knowledge base.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        wiki_query = st.text_input("What would you like to research today?", key="wiki_input", 
                                 placeholder="Enter a search term (works best with specific topics)")
    with col2:
        search_wiki = st.button("🔍 Search Wikipedia", use_container_width=True)
    
    if search_wiki and wiki_query:
        # Add to search history
        st.session_state.search_history.append(f"Wiki: {wiki_query}")
        
        with st.spinner("📡 Establishing Connection..."):
            target_string = wiki_query.replace(" ", "+")
            search_string = f"https://en.wikipedia.org/wiki/{target_string}"
            data = requests.get(search_string)
            time.sleep(0.5)
            
            # Create a status indicator
            if data.status_code == 200:
                st.success(f"Connection Successful (Status: {data.status_code}) ✅")
                souping = bs4.BeautifulSoup(data.text, "html.parser")
                heading = souping.select("#firstHeading")
                
                # Display results in a stylized container
                with st.container():
                    st.markdown('<div class="search-results">', unsafe_allow_html=True)
                    
                    if heading:
                        st.markdown(f'<div class="result-header">{heading[0].getText()}</div>', unsafe_allow_html=True)
                    
                    # Show a progress bar while processing paragraphs
                    progress_bar = st.progress(0)
                    paragraphs = souping.select("p")
                    st.session_state.data_storage = []
                    
                    # Only display first 10 paragraphs to keep it manageable
                    max_paragraphs = min(10, len(paragraphs))
                    for i, val in enumerate(paragraphs[:max_paragraphs]):
                        text = val.getText().strip()
                        if text:  # Only add non-empty paragraphs
                            st.write(text)
                            st.session_state.data_storage.append(text)
                        progress_bar.progress((i + 1) / max_paragraphs)
                    
                    if len(paragraphs) > max_paragraphs:
                        st.info(f"Showing first {max_paragraphs} of {len(paragraphs)} paragraphs. Save results to view all.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Connection Failed")
                st.warning("1. Please check your internet connection\n2. Make sure you entered a valid search term\n3. Wikipedia works best with specific topics")

# AI Search Tab
with tab2:
    st.header("DuckDuckGo AI Search")
    st.write("Get concise answers powered by DuckDuckGo's AI engine.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        duck_query = st.text_input("What would you like to know?", key="duck_input", 
                                  placeholder="Ask any question...")
    with col2:
        search_duck = st.button("🔍 AI Search", use_container_width=True)
    
    if search_duck and duck_query:
        # Add to search history
        st.session_state.search_history.append(f"AI: {duck_query}")
        
        with st.spinner("🤖 Searching the web for an answer..."):
            try:
                # Configure Chrome options for headless mode
                from selenium.webdriver.chrome.options import Options
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                driver = webdriver.Chrome(options=chrome_options)
                formatted_query = duck_query.replace(" ", "+")
                driver.get(f"https://duckduckgo.com/?t=ffab&q={formatted_query}&ia=web&assist=true")
                
                element = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[6]/div[4]/div/div/div/div[2]/section[1]/ol/li[1]/div/div/div/div/div[2]/div[1]/div/p'))
                )
                
                st.session_state.data_bucket = [element.text]
                
                # Display the result with nice formatting
                st.markdown('<div class="search-results">', unsafe_allow_html=True)
                st.success("✨ Here's what I found:")
                st.markdown(f"<p style='font-size: 1.1rem; padding: 10px;'>{element.text}</p>", unsafe_allow_html=True)
                st.caption("Source: DuckDuckGo")
                st.markdown('</div>', unsafe_allow_html=True)
                
                driver.quit()
                
            except TimeoutException:
                st.error("Search timed out! The results might not be available or your internet connection is slow.")
                try:
                    driver.quit()
                except:
                    pass
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                try:
                    driver.quit()
                except:
                    pass

# Save Data Tab
with tab3:
    st.header("Save and Export Results")
    st.write("Save your search results for later reference.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Wikipedia Research Data")
        
        # Display a preview of data
        if st.session_state.data_storage:
            with st.expander("Preview Wikipedia Data"):
                for idx, item in enumerate(st.session_state.data_storage[:3]):
                    st.write(f"{idx+1}. {item[:100]}...")
                if len(st.session_state.data_storage) > 3:
                    st.write(f"... and {len(st.session_state.data_storage) - 3} more items")
        
        wiki_button = st.button("💾 Save Wikipedia Results", use_container_width=True)
        
        if wiki_button:
            if st.session_state.data_storage:
                try:
                    with open('wiki_results.txt', 'w', encoding='utf-8') as new_file:
                        for item in st.session_state.data_storage:
                            new_file.write(f"{item}\n\n")
                    
                    # Create a download button
                    with open('wiki_results.txt', 'r', encoding='utf-8') as file:
                        btn = st.download_button(
                            label="📥 Download Wikipedia Results",
                            data=file,
                            file_name="wiki_results.txt",
                            mime="text/plain"
                        )
                    
                    st.success("Wikipedia data saved successfully!")
                except Exception as e:
                    st.error(f"Save failed: {str(e)}")
            else:
                st.warning("⚠️ No Wikipedia data to save. Perform a search first.")
    
    with col2:
        st.subheader("AI Search Results")
        
        # Display a preview of data
        if st.session_state.data_bucket:
            with st.expander("Preview AI Search Data"):
                for idx, item in enumerate(st.session_state.data_bucket):
                    st.write(f"{idx+1}. {item[:100]}...")
        
        ai_button = st.button("💾 Save AI Search Results", use_container_width=True)
        
        if ai_button:
            if st.session_state.data_bucket:
                try:
                    with open('ai_results.txt', 'w', encoding='utf-8') as new_files:
                        for item in st.session_state.data_bucket:
                            new_files.write(f"{item}\n\n")
                    
                    # Create a download button
                    with open('ai_results.txt', 'r', encoding='utf-8') as file:
                        btn = st.download_button(
                            label="📥 Download AI Search Results",
                            data=file,
                            file_name="ai_results.txt",
                            mime="text/plain"
                        )
                    
                    st.success("AI search data saved successfully!")
                except Exception as e:
                    st.error(f"Save failed: {str(e)}")
            else:
                st.warning("⚠️ No AI search data to save. Perform a search first.")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 10px; background-color: #f1f3f4; border-radius: 10px;">
    <p style="color: #5f6368; font-size: 1.0rem; margin-top: 5px">Searchly © 2025 | Powered by Streamlit, Wikipedia & DuckDuckGo</p>
</div>
""", unsafe_allow_html=True)