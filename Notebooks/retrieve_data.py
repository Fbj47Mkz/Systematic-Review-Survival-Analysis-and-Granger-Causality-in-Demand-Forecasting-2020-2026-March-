#!/usr/bin/env python3
"""
Bibliometric Data Retrieval Script
===================================
Systematic Literature Review: Survival Analysis and Causality in Demand Forecasting
Data sources: CrossRef, arXiv, PubMed
Date range: 2020-2026
"""

import requests
import json
import time
import pandas as pd
import xml.etree.ElementTree as ET
import urllib.parse
import os

# Create directories
os.makedirs("downloads/raw", exist_ok=True)
os.makedirs("downloads/processed", exist_ok=True)

# ========================
# CROSSREF API FUNCTIONS
# ========================

def search_crossref(query_string, year_range, max_results=100):
    """Search CrossRef API for papers."""
    base_url = "https://api.crossref.org/works"
    
    params = {
        'query': query_string,
        'filter': f'from-pub-date:{year_range[0]},until-pub-date:{year_range[1]}',
        'rows': max_results,
        'mailto': 'research@example.org'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['message']['items']
    except Exception as e:
        print(f"Error in CrossRef search: {e}")
        return []

# CrossRef queries
crossref_queries = [
    "survival analysis customer churn",
    "survival analysis demand forecasting",
    "hazard model customer lifetime",
    "Cox regression churn prediction",
    "time-to-event customer forecasting",
    "causal inference demand forecasting",
    "causal inference sales prediction",
    "Granger causality demand",
    "causal machine learning customer",
    "deep survival learning",
    "neural survival analysis"
]

print("Retrieving CrossRef data...")
crossref_results = []
for query in crossref_queries:
    print(f"  Query: {query}")
    results = search_crossref(query, (2020, 2026), max_results=100)
    print(f"    Found: {len(results)} results")
    crossref_results.extend(results)
    time.sleep(1)

# Deduplicate by DOI
seen_dois = set()
unique_crossref = []
for item in crossref_results:
    doi = item.get('DOI')
    if doi and doi not in seen_dois:
        seen_dois.add(doi)
        unique_crossref.append(item)
    elif not doi:
        unique_crossref.append(item)

print(f"Total unique CrossRef results: {len(unique_crossref)}")

# Save raw CrossRef data
with open("downloads/raw/crossref_all_results.json", "w") as f:
    json.dump(unique_crossref, f, indent=2)

# ========================
# ARXIV API FUNCTIONS
# ========================

def search_arxiv(query, max_results=200):
    """Search arXiv API."""
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        'search_query': f"all:{query}",
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {
            'atom': 'http://www.w3.org/2006/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        entries = []
        for entry in root.findall('atom:entry', ns):
            paper = {}
            paper['id'] = entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else None
            paper['title'] = entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else None
            paper['summary'] = entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else None
            paper['published'] = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else None
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text)
            paper['authors'] = authors
            
            # Categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories
            
            # Filter by year
            if paper['published']:
                pub_year = int(paper['published'][:4])
                if 2020 <= pub_year <= 2026:
                    entries.append(paper)
        
        return entries
    except Exception as e:
        print(f"Error in arXiv search: {e}")
        return []

# arXiv queries
arxiv_queries = [
    "survival+analysis+demand",
    "survival+analysis+customer",
    "causal+inference+forecasting",
    "deep+survival+learning"
]

print("\nRetrieving arXiv data...")
arxiv_results = []
for query in arxiv_queries:
    print(f"  Query: {query}")
    results = search_arxiv(query, max_results=200)
    print(f"    Found: {len(results)} results (2020-2026)")
    arxiv_results.extend(results)
    time.sleep(3)

print(f"Total arXiv results: {len(arxiv_results)}")

# Save raw arXiv data
with open("downloads/raw/arxiv_raw_results.json", "w") as f:
    json.dump(arxiv_results, f, indent=2)

# ========================
# PUBMED API FUNCTIONS
# ========================

def search_pubmed(query, year_start, year_end, max_results=100):
    """Search PubMed using E-utilities API."""
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    search_params = {
        'db': 'pubmed',
        'term': f"{query} AND {year_start}:{year_end}[dp]",
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance'
    }
    
    try:
        response = requests.get(search_url, params=search_params, timeout=30)
        response.raise_for_status()
        search_data = response.json()
        
        pmids = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            return None
        
        time.sleep(0.5)
        
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        response = requests.get(fetch_url, params=fetch_params, timeout=60)
        response.raise_for_status()
        
        return response.content
        
    except Exception as e:
        print(f"Error in PubMed search: {e}")
        return None

# PubMed queries
pubmed_queries = [
    "survival analysis business forecasting",
    "survival analysis customer churn",
    "survival analysis demand prediction",
    "time-to-event marketing",
    "Cox model customer",
    "causal inference forecasting -cancer -clinical -trial"
]

print("\nRetrieving PubMed data...")
for idx, query in enumerate(pubmed_queries):
    print(f"  Query: {query}")
    xml_result = search_pubmed(query, 2020, 2026, max_results=100)
    if xml_result:
        filename = f"downloads/raw/pubmed_results_{idx}.xml"
        with open(filename, 'wb') as f:
            f.write(xml_result)
        print(f"    Saved: {filename}")
    time.sleep(1)

print("\nData retrieval complete!")
print("Raw data saved to downloads/raw/")
