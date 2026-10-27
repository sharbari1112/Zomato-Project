# Problem Statement

## Project Context

This project delivers an **AI-powered restaurant recommendation service** modeled on Zomato. People already have large catalogs of restaurants, ratings, cuisines, and prices, but they still spend time scanning lists that do not match how they actually decide: a neighborhood, a budget, a cuisine, a minimum rating, and extra constraints such as family-friendly or quick service.

The application closes that gap by combining a **real-world restaurant dataset** with a **Large Language Model (LLM)**. Structured filters narrow the catalog to relevant options; the LLM then ranks those options and explains them in natural language so the output feels like a personalized suggestion, not a raw table dump.

The dataset source is the Hugging Face collection [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation).

## Problem

Restaurant discovery is a multi-constraint matching problem:

- Preferences are mixed (location, budget band, cuisine, rating floor, and qualitative notes).
- Catalog data is structured (name, location, cuisine, cost, rating), while explanations users want are unstructured.
- Rankings without reasons are hard to trust; reasons without data are easy to hallucinate.

A useful system must **filter on facts first**, then **use an LLM only on the shortlist** so recommendations stay grounded in the dataset while remaining readable and personal.

## Objective

Design and implement an application that:

1. Takes user preferences such as location, budget, cuisine, and ratings.
2. Uses a real-world dataset of restaurants.
3. Leverages an LLM to generate personalized, human-like recommendations.
4. Displays clear, useful results to the user.

## System Workflow

### 1. Data ingestion

- Load and preprocess the Zomato dataset from Hugging Face.
- Extract fields needed for matching and display, including restaurant name, location, cuisine, cost, and rating.

### 2. User input

Collect preferences, for example:

| Preference | Example |
| --- | --- |
| Location | Delhi, Bangalore |
| Budget | low, medium, high |
| Cuisine | Italian, Chinese |
| Minimum rating | numeric floor chosen by the user |
| Additional notes | family-friendly, quick service |

### 3. Integration layer

- Filter and prepare restaurant rows that match the user’s structured input.
- Pass that structured shortlist into an LLM prompt.
- Design the prompt so the model can reason over the candidates and rank them, rather than inventing restaurants.

### 4. Recommendation engine

The LLM should:

- Rank restaurants from the filtered set.
- Explain why each recommendation fits the stated preferences.
- Optionally summarize the overall set of choices.

### 5. Output display

Present the top recommendations in a user-friendly format with at least:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

## Success Criteria

The solution is successful when a user can state preferences, receive a short ranked list drawn from the dataset, and understand *why* each option was chosen—without needing to inspect the raw catalog themselves.
