import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import quote

# Configure the page
st.set_page_config(
    page_title="PriceScout - Compare Prices Across Sites",
    page_icon="🔍",
    layout="wide"
)

# CSS for better styling
st.markdown("""
<style>
    .product-card {
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        background-color: white;
    }
    .price {
        font-size: 20px;
        font-weight: bold;
        color: #ff5722;
    }
    .site-tag {
        background-color: #f1f1f1;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 12px;
        margin-right: 5px;
    }
    .best-price {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
    }
    .header-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("""
<div class="header-container">
    <h1 style="color:#3f51b5;">PriceScout 🔍</h1>
    <p>Find the best deals across Amazon, Flipkart, Snapdeal and more!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar filters
st.sidebar.header("Filters")
price_range = st.sidebar.slider("Price Range (₹)", 0, 100000, (0, 50000))
sort_by = st.sidebar.selectbox("Sort By", ["Price: Low to High", "Price: High to Low", "Popularity", "Newest First"])
include_sites = st.sidebar.multiselect("Include Sites", ["Amazon", "Flipkart", "Snapdeal", "Croma", "Reliance Digital"], 
                                      default=["Amazon", "Flipkart", "Snapdeal"])

# Mock affiliate link generator (in production, you'd use actual affiliate links)
def get_affiliate_link(site, product_url):
    # Your affiliate IDs would go here
    affiliate_ids = {
        "Amazon": "youraffid-21",
        "Flipkart": "yourflipkartaffid",
        "Snapdeal": "yoursnpaffid",
        "Croma": "yourcromaaffid",
        "Reliance Digital": "yourrelaffid"
    }
    
    if site == "Amazon":
        return f"{product_url}&tag={affiliate_ids['Amazon']}"
    elif site == "Flipkart":
        return f"{product_url}&affid={affiliate_ids['Flipkart']}"
    else:
        # Generic approach for other sites
        separator = "&" if "?" in product_url else "?"
        return f"{product_url}{separator}affid={affiliate_ids.get(site, 'generic')}"

# Mock scraper function (in production, you'd implement actual scraping)
def search_products(query, sites=None):
    """
    This function simulates scraping product data from various e-commerce sites.
    In production, you would implement actual web scraping or API calls.
    """
    # Simulate API delay
    time.sleep(1)
    
    # Mock product data
    mock_products = [
        {"site": "Amazon", "name": f"Samsung 8 Kg Washing Machine - Fully Automatic", "price": 24999, "rating": 4.3, 
         "url": "https://www.amazon.in/product/B08XXXXX", "image": "https://m.media-amazon.com/images/placeholder.jpg"},
        {"site": "Flipkart", "name": f"Samsung 8 Kg Fully-Automatic Front Load", "price": 23499, "rating": 4.5, 
         "url": "https://www.flipkart.com/product/p/XXXXX", "image": "https://rukminim1.flixcart.com/placeholder.jpg"},
        {"site": "Snapdeal", "name": f"Samsung 8Kg Front Load Fully Automatic", "price": 25990, "rating": 4.2, 
         "url": "https://www.snapdeal.com/product/XXXXX", "image": "https://n3.sdlcdn.com/placeholder.jpg"},
        {"site": "Amazon", "name": f"LG 7 Kg Washing Machine - Fully Automatic", "price": 22490, "rating": 4.4, 
         "url": "https://www.amazon.in/product/B08YYYYY", "image": "https://m.media-amazon.com/images/placeholder2.jpg"},
        {"site": "Flipkart", "name": f"LG 7 Kg 5 Star Inverter Front Load", "price": 21999, "rating": 4.6, 
         "url": "https://www.flipkart.com/product/p/YYYYY", "image": "https://rukminim1.flixcart.com/placeholder2.jpg"},
        {"site": "Croma", "name": f"LG 7 Kg Smart Inverter Washer", "price": 23990, "rating": 4.3, 
         "url": "https://www.croma.com/product/ZZZZZ", "image": "https://cdn.croma.com/placeholder.jpg"},
        {"site": "Reliance Digital", "name": f"Whirlpool 7.5 Kg 5 Star Royal", "price": 22499, "rating": 4.1, 
         "url": "https://www.reliancedigital.in/product/AAAAA", "image": "https://www.reliancedigital.in/placeholder.jpg"},
        {"site": "Amazon", "name": f"Whirlpool 7.5 Kg 5 Star Royal Plus", "price": 22990, "rating": 4.3, 
         "url": "https://www.amazon.in/product/B08AAAAA", "image": "https://m.media-amazon.com/images/placeholder3.jpg"},
    ]
    
    # Filter by selected sites
    if sites:
        mock_products = [p for p in mock_products if p["site"] in sites]
    
    # Filter by price range
    mock_products = [p for p in mock_products if price_range[0] <= p["price"] <= price_range[1]]
    
    # Sort products
    if sort_by == "Price: Low to High":
        mock_products.sort(key=lambda x: x["price"])
    elif sort_by == "Price: High to Low":
        mock_products.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "Popularity":
        mock_products.sort(key=lambda x: x["rating"], reverse=True)
    
    # Add affiliate links
    for product in mock_products:
        product["affiliate_url"] = get_affiliate_link(product["site"], product["url"])
        
    return mock_products

# Search functionality
search_query = st.text_input("What are you looking for?", "washing machine")
brands = st.multiselect("Select Brands", ["Samsung", "LG", "Whirlpool", "Bosch", "IFB"], 
                       default=["Samsung", "LG", "Whirlpool"])

if st.button("Search", type="primary") or search_query:
    st.subheader("Search Results")
    
    with st.spinner("Searching across multiple sites..."):
        products = search_products(search_query, include_sites)
        
        # Filter by selected brands
        if brands:
            products = [p for p in products if any(brand.lower() in p["name"].lower() for brand in brands)]
        
    if not products:
        st.warning("No products found matching your criteria. Try adjusting your filters.")
    else:
        # Find the cheapest product
        cheapest_product = min(products, key=lambda x: x["price"])
        
        # Display products in columns
        cols = st.columns(1)
        
        for i, product in enumerate(products):
            with cols[0]:
                # Add best price highlight
                card_class = "product-card best-price" if product["price"] == cheapest_product["price"] else "product-card"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display:flex; align-items:start;">
                        <div style="flex:1;">
                            <span class="site-tag">{product["site"]}</span>
                            <h3>{product["name"]}</h3>
                            <p class="price">₹{product["price"]}</p>
                            <p>⭐ {product["rating"]}/5</p>
                            <a href="{product["affiliate_url"]}" target="_blank">
                                <button style="background-color:#ff9800; color:white; border:none; padding:8px 15px; 
                                border-radius:4px; cursor:pointer;">
                                    View Deal
                                </button>
                            </a>
                            {"<span style='background-color:#4caf50; color:white; padding:3px 8px; border-radius:3px; font-size:12px; margin-left:10px;'>BEST PRICE</span>" 
                            if product["price"] == cheapest_product["price"] else ""}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)

# Price trend chart (mock data)
st.subheader("Price Trends")
if search_query:
    chart_data = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=90, freq='D'),
        'Amazon': [random.randint(22000, 26000) for _ in range(90)],
        'Flipkart': [random.randint(21000, 25000) for _ in range(90)],
        'Snapdeal': [random.randint(23000, 27000) for _ in range(90)]
    })
    
    chart_data.set_index('Date', inplace=True)
    st.line_chart(chart_data)

# FAQ section
with st.expander("Frequently Asked Questions"):
    st.markdown("""
    **How does PriceScout work?**
    
    PriceScout searches across multiple e-commerce websites to find the best prices for the products you're looking for. We compare prices, ratings, and availability to help you make informed purchasing decisions.
    
    **Do I pay more when I buy through PriceScout?**
    
    No! The prices you see are exactly the same as on the original websites. We earn a small commission from the retailers when you make a purchase, which helps us keep this service free for you.
    
    **Are the prices always up-to-date?**
    
    We strive to provide the most current pricing information, but prices can change rapidly. We recommend clicking through to verify the final price before making your purchase.
    """)

# Footer
st.markdown("""
<div style="text-align:center; margin-top:50px; padding:20px; background-color:#f8f9fa; border-radius:5px;">
    <p>© 2025 PriceScout | All prices are inclusive of taxes | We are not affiliated with any of the retailers mentioned.</p>
    <p style="font-size:12px;">This website uses affiliate links. When you click on links and make purchases, we may earn a commission.</p>
</div>
""", unsafe_allow_html=True)
