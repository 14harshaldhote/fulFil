#!/usr/bin/env python3
"""
Generate a single comprehensive CSV file with 500K+ products.
Includes all test scenarios: duplicates, invalid rows, edge cases, etc.
"""

import csv
import random
import os
from decimal import Decimal

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_ROWS = 510000  # 510K to be safe

# Sample data for realistic products
CATEGORIES = ["Electronics", "Clothing", "Home", "Sports", "Books", "Toys", "Food", "Beauty", "Auto", "Garden"]
BRANDS = ["Apple", "Samsung", "Nike", "Sony", "LG", "HP", "Dell", "Lenovo", "Adidas", "Puma", "Asus", "Bose", "Canon", "Nikon"]
PRODUCTS = ["Phone", "Laptop", "Tablet", "Watch", "Headphones", "Camera", "Speaker", "TV", "Monitor", "Keyboard", "Mouse", "Charger", "Cable", "Case", "Stand"]
ADJECTIVES = ["Pro", "Max", "Ultra", "Mini", "Lite", "Plus", "Air", "Elite", "Premium", "Basic"]


def generate_sku(index, case_variant=False):
    """Generate SKU with optional case variation for duplicates"""
    if case_variant:
        variants = [f"SKU-{index:06d}", f"sku-{index:06d}", f"Sku-{index:06d}", f"sKu-{index:06d}"]
        return random.choice(variants)
    return f"SKU-{index:06d}"


def generate_name():
    return f"{random.choice(BRANDS)} {random.choice(ADJECTIVES)} {random.choice(PRODUCTS)}"


def generate_description():
    return f"High quality {random.choice(CATEGORIES).lower()} product. Fast shipping. Warranty included."


def generate_price():
    return round(random.uniform(9.99, 2999.99), 2)


def main():
    print(f"\n🔧 Generating {TARGET_ROWS:,} products CSV...\n")
    
    rows = []
    duplicate_indices = set()
    
    # Generate main products (500K unique)
    for i in range(1, 500001):
        rows.append([
            generate_sku(i),
            generate_name(),
            generate_description(),
            generate_price()
        ])
        
        if i % 100000 == 0:
            print(f"   ✓ Generated {i:,} products...")
    
    print("\n📝 Adding test scenarios...\n")
    
    # Add ~5000 duplicate SKUs with different cases (to test overwrite)
    print("   Adding 5000 duplicate SKUs (case variations)...")
    for i in range(1, 5001):
        rows.append([
            generate_sku(i, case_variant=True),  # Will be duplicate of existing SKU
            f"UPDATED: {generate_name()}",
            f"OVERWRITTEN: {generate_description()}",
            generate_price()
        ])
    
    # Add ~500 rows with missing SKU (should fail)
    print("   Adding 500 invalid rows (missing SKU)...")
    for _ in range(500):
        rows.append([
            "",  # Empty SKU - should be skipped
            generate_name(),
            generate_description(),
            generate_price()
        ])
    
    # Add ~500 rows with whitespace SKU (should fail)
    print("   Adding 500 invalid rows (whitespace SKU)...")
    for _ in range(500):
        rows.append([
            "   ",  # Whitespace SKU - should be skipped
            generate_name(),
            generate_description(),
            generate_price()
        ])
    
    # Add ~1000 rows with edge cases
    print("   Adding 1000 edge case rows...")
    edge_cases = [
        # Unicode names and descriptions
        ["SKU-UNICODE-001", "日本語製品 Product", "Japanese description テスト", 199.99],
        ["SKU-UNICODE-002", "Émoji 🎉 Product", "Fun product with émojis 🚀", 49.99],
        ["SKU-UNICODE-003", "Ñoño Español", "Descripción en español", 79.99],
        ["SKU-UNICODE-004", "中文产品名称", "Chinese product description", 149.99],
        ["SKU-UNICODE-005", "العربية منتج", "Arabic product test", 99.99],
        
        # Special characters
        ["SKU-SPECIAL-001", "Product with \"quotes\"", "Description with 'single quotes'", 29.99],
        ["SKU-SPECIAL-002", "Product, with, commas", "Description, also, has, commas", 39.99],
        ["SKU-SPECIAL-003", "Product & Ampersand", "Description <with> HTML chars", 49.99],
        
        # Long content
        ["SKU-LONG-001", "A" * 200, "Very long name test", 59.99],
        ["SKU-LONG-002", "Normal Name", "B" * 500, 69.99],
        
        # Missing optional fields
        ["SKU-NO-NAME", "", "Product without name", 19.99],
        ["SKU-NO-DESC", "Product without description", "", 29.99],
        
        # Price edge cases
        ["SKU-ZERO-PRICE", "Free Product", "Zero price test", 0.00],
        ["SKU-BAD-PRICE-1", "Bad price product", "Invalid price", "abc"],
        ["SKU-BAD-PRICE-2", "Negative price", "Should handle", -50.00],
        
        # Whitespace in content
        ["  SKU-WHITESPACE  ", "  Whitespace in SKU  ", "  Spaces around content  ", 99.99],
    ]
    
    # Add edge cases multiple times to have ~1000
    for _ in range(60):
        rows.extend(edge_cases)
    
    # Add some more unique products to hit 510K+
    print("   Adding remaining products to reach 510K+...")
    current = len(rows)
    for i in range(500001, 500001 + (TARGET_ROWS - current) + 1000):
        rows.append([
            generate_sku(i),
            generate_name(),
            generate_description(),
            generate_price()
        ])
    
    # Shuffle to mix all cases throughout the file
    print("\n🔀 Shuffling rows...")
    random.shuffle(rows)
    
    # Write to CSV
    filepath = os.path.join(OUTPUT_DIR, "products_500k_all_tests.csv")
    
    print(f"\n💾 Writing {len(rows):,} rows to CSV...")
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sku', 'name', 'description', 'price'])
        writer.writerows(rows)
    
    # Get file size
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    print(f"\n✅ Done!")
    print(f"   File: {filepath}")
    print(f"   Rows: {len(rows):,}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"\n📋 Test scenarios included:")
    print(f"   • 500,000 unique products")
    print(f"   • 5,000 duplicate SKUs (case variations for overwrite test)")
    print(f"   • 500 missing SKU rows (should be skipped)")
    print(f"   • 500 whitespace SKU rows (should be skipped)")
    print(f"   • 1,000+ edge cases (unicode, special chars, long content)")
    print(f"   • All rows shuffled randomly")


if __name__ == "__main__":
    main()
