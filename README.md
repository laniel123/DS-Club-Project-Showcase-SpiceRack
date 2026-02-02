# DS-Club-Project-Showcase-SpiceRack


# SpiceRack 
*A spice-based recipe recommendation system*

## Overview
SpiceRack is a data-driven project that helps users discover recipes based on the spices they already have. Instead of starting from full ingredient lists, the system focuses on **spice overlap** to recommend recipes that are realistic and easy to cook with existing pantry items.

This project was developed for the Data Science Club Project Showcase and emphasizes interpretability, modular design, and iterative model development.

---

## Project Goal
The goal of this project is to:
- Analyze large-scale recipe data
- Extract and normalize spice information from recipes
- Build a preliminary recommendation model that maps user-owned spices to relevant recipes

---

## Dataset
This project uses the **RecipeNLG** dataset, a large, cleaned collection of over 2 million recipes designed for structured text and ingredient analysis.

> Due to file size constraints, raw datasets are **not included** in this repository.

### Dataset Setup
1. Download the RecipeNLG dataset from its official source.
2. Place the dataset locally (e.g., in a `data/` folder).
3. Update file paths in the notebook as needed.

---

## Methodology (Preliminary Model)
The preliminary model is a **similarity-based recommender system**:

1. Each recipe is represented as a set of spices extracted from its ingredient list.
2. User input is provided as a list of available spices.
3. Recipes are ranked using **Jaccard similarity** based on spice overlap.
4. The system outputs the top recommended recipes along with similarity scores.

This baseline model serves as a proof of concept and foundation for future improvements.

---

## Repository Structure